"""Frame-level inference wrapper for real-time camera recognition.

Provides three core functions that together form the online inference pipeline
without touching the filesystem.  Designed to be called from the PyQt5 camera
loop, but also usable from other real-time / streaming contexts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .dataset_builder import FEATURE_COLUMNS
from .feature_glcm import extract_glcm_features
from .feature_hsv import extract_hsv_features
from .ml_classifier import (
    load_model,
    predict_single,
    validate_model_classes,
)
from .preprocessing import preprocess_image
from .rule_classifier import classify_by_rules
from .segmentation import segment_banana
from .utils import merge_dicts, resolve_path

# ---------------------------------------------------------------------------
# Method name → model filename mapping (mirrors app_pyqt.py)
# ---------------------------------------------------------------------------
METHOD_TO_MODEL: dict[str, str] = {
    "KNN": "knn_model.pkl",
    "SVM": "svm_model.pkl",
    "Logistic": "logistic_model.pkl",
}


# ---------------------------------------------------------------------------
# Frame-level feature extraction
# ---------------------------------------------------------------------------


def extract_features_for_frame(
    frame_bgr: np.ndarray,
    config: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Extract HSV + GLCM features from an in-memory BGR camera frame.

    This is the online analogue of
    :func:`dataset_builder.extract_features_for_image` but operates on a
    ``np.ndarray`` instead of a file path.  All core algorithm calls
    (preprocessing, segmentation, HSV/GLCM extraction) are delegated to the
    existing modules — no logic is duplicated.

    Parameters
    ----------
    frame_bgr : np.ndarray
        Camera frame in BGR colour space (height × width × 3, uint8).
    config : dict
        Full project configuration dict (see ``config.yaml``).

    Returns
    -------
    features : dict
        Dictionary of extracted features.  Includes all keys from
        ``FEATURE_COLUMNS`` plus ``rule_prediction``, ``mask_area``,
        ``brown_ratio``, ``banana_color_ratio``, ``yellow_green_ratio``.
    processed : np.ndarray
        Preprocessed BGR image (resized, blurred, equalised).
    mask : np.ndarray
        Binary banana segmentation mask (same spatial size as ``processed``).
    """
    # ---- preprocessing --------------------------------------------------
    prep_cfg = config.get("preprocessing", {})
    cam_prep_cfg = config.get("camera_preprocessing", {})
    camera_cfg = config.get("camera", {})

    realtime_max_size = int(camera_cfg.get("realtime_max_size", 640))

    # Camera mode: apply white balance to reduce ambient-light colour shifts.
    use_wb = bool(cam_prep_cfg.get("white_balance", True))
    wb_pct = float(cam_prep_cfg.get("wb_percentile", 1.0))

    processed = preprocess_image(
        frame_bgr,
        max_size=realtime_max_size,
        blur_kernel=int(cam_prep_cfg.get("blur_kernel", prep_cfg.get("blur_kernel", 5))),
        equalize=bool(cam_prep_cfg.get("equalize", True)),
        white_balance=use_wb,
        wb_percentile=wb_pct,
    )

    # ---- segmentation ---------------------------------------------------
    seg_cfg = config.get("segmentation", {})
    mask, color_masks = segment_banana(
        processed,
        min_area_ratio=float(seg_cfg.get("min_area_ratio", 0.01)),
        morphology_kernel=int(seg_cfg.get("morphology_kernel", 7)),
    )
    # color_masks: {"green", "yellow", "brown", "dark"} — each uint8 0/255

    # ---- feature extraction ---------------------------------------------
    feat_cfg = config.get("features", {})
    hsv_features = extract_hsv_features(processed, mask)
    glcm_features = extract_glcm_features(
        processed,
        mask,
        levels=int(feat_cfg.get("glcm_levels", 32)),
        distances=feat_cfg.get("glcm_distances", [1, 2]),
    )
    features = merge_dicts(hsv_features, glcm_features)

    # ---- extra colour ratios for candidate validation -------------------
    mask_pixels = max(int((mask > 0).sum()), 1)

    brown_pixels = int(cv2.countNonZero(cv2.bitwise_and(color_masks["brown"], mask)))
    green_pixels = int(cv2.countNonZero(cv2.bitwise_and(color_masks["green"], mask)))
    yellow_pixels = int(cv2.countNonZero(cv2.bitwise_and(color_masks["yellow"], mask)))

    features["brown_ratio"] = brown_pixels / mask_pixels
    features["banana_color_ratio"] = (green_pixels + yellow_pixels + brown_pixels) / mask_pixels
    features["yellow_green_ratio"] = (green_pixels + yellow_pixels) / mask_pixels

    # ---- rule-based baseline (camera-specific thresholds) ---------------
    # Camera mode uses `camera_rules` (if present) to compensate for
    # sensor noise, auto-exposure colour shifts, and higher texture.
    # Falls back to static `rules` if no camera-specific config exists.
    camera_rules = config.get("camera_rules") or config.get("rules", {})
    rule_prediction = classify_by_rules(features, camera_rules)
    features["rule_prediction"] = rule_prediction
    features["mask_area"] = mask_pixels

    return features, processed, mask


# ---------------------------------------------------------------------------
# Prediction dispatcher (rule-based + ML with automatic fallback)
# ---------------------------------------------------------------------------


def predict_features(
    features: dict[str, Any],
    config: dict[str, Any],
    method: str,
    model_cache: dict[str, Any] | None = None,
) -> tuple[str, dict[str, float], str]:
    """Predict banana ripeness from a pre-computed feature dict.

    Parameters
    ----------
    features : dict
        Feature dictionary (output of :func:`extract_features_for_frame`).
    config : dict
        Project configuration dict.
    method : str
        One of ``"规则分类"``, ``"KNN"``.
    model_cache : dict or None
        Mutable cache for loaded ML models.

    Returns
    -------
    prediction : str
        Predicted class label.
    proba : dict
        Class probability dictionary (empty for rule-based / fallback).
    method_used : str
        Actual classification method — may differ from *method* when
        automatic fallback occurred.
    """
    if model_cache is None:
        model_cache = {}

    # -- rule-based (always available) ------------------------------------
    if method == "规则分类":
        prediction = features.get(
            "rule_prediction",
            classify_by_rules(features, config.get("rules", {})),
        )
        return prediction, {}, "规则分类"

    # -- ML methods -------------------------------------------------------
    model_filename = METHOD_TO_MODEL.get(method)
    if model_filename is None:
        prediction = features.get(
            "rule_prediction",
            classify_by_rules(features, config.get("rules", {})),
        )
        return prediction, {}, "规则分类（未知方法回退）"

    # Load / retrieve cached model
    if method in model_cache:
        model = model_cache[method]
    else:
        model_dir_path = config.get("paths", {}).get("model_dir", "models")
        model_dir = resolve_path(model_dir_path)
        model_path = model_dir / model_filename
        if not model_path.exists():
            prediction = features.get(
                "rule_prediction",
                classify_by_rules(features, config.get("rules", {})),
            )
            return prediction, {}, f"规则分类（{method} 模型文件不存在）"
        model = load_model(model_path)
        model_cache[method] = model

    # Validate that the model covers all three ripeness classes.
    # A single-class debug model always predicts one label at 100 %.
    valid, reason = validate_model_classes(model)
    if not valid:
        prediction = features.get(
            "rule_prediction",
            classify_by_rules(features, config.get("rules", {})),
        )
        return prediction, {}, f"规则分类（{method} 模型类别不完整: {reason}）"
    try:
        prediction, proba = predict_single(model, features)
        return prediction, proba, method
    except Exception:
        prediction = features.get(
            "rule_prediction",
            classify_by_rules(features, config.get("rules", {})),
        )
        return prediction, {}, f"规则分类（{method} 预测异常回退）"


# ---------------------------------------------------------------------------
# Banana candidate validation (strict multi-condition gate)
# ---------------------------------------------------------------------------

_DEFAULT_CANDIDATE: dict[str, Any] = {
    "min_area_ratio": 0.01,
    "max_area_ratio": 0.45,
    "min_banana_color_ratio": 0.22,
    "min_yellow_green_ratio": 0.15,
    "max_dark_ratio_for_presence": 0.65,
    "min_rotated_aspect": 1.4,
    "max_rotated_aspect": 8.0,
    "min_extent": 0.28,
    "use_center_roi": True,
    "roi_width_ratio": 0.70,
    "roi_height_ratio": 0.70,
}


def is_valid_banana_candidate(
    features: dict[str, Any],
    mask: np.ndarray,
    image_shape: tuple[int, ...],
    config: dict[str, Any],
) -> tuple[bool, str]:
    """Strict multi-condition check: does the segmented region contain a banana?

    **Design principle**: ``dark_ratio`` is deliberately excluded from the
    banana-presence colour check.  Dark pixels (shadows, black clothing,
    screens, dark furniture) can dominate non-banana segmentations, so
    presence is gated on *green + yellow + brown*.  ``dark_ratio`` is only
    used as an *upper-bound veto* (if > 65 % of the mask is dark, it is
    unlikely to be a banana).

    Checks (in order):

    1. **mask area ratio** —  1 % ≤ area / image ≤ 45 %
    2. **rotated bounding-box aspect** — 1.4 ≤ long/short ≤ 8.0
    3. **extent** — mask_area / rotated_rect_area ≥ 0.25
    4. **banana colour ratio** — (green + yellow + brown) ≥ 20 % of mask
    5. **yellow-green ratio** — (green + yellow) ≥ 12 % of mask
    6. **dark-ratio veto** — dark ≤ 65 % of mask
    7. **center ROI** — mask centre must lie in a configurable central window

    Parameters
    ----------
    features : dict
        Feature dict from :func:`extract_features_for_frame`.  Required keys:
        ``mask_area``, ``green_ratio``, ``yellow_ratio``, ``dark_ratio``,
        ``brown_ratio``, ``banana_color_ratio``, ``yellow_green_ratio``.
    mask : np.ndarray
        Binary segmentation mask (uint8, 0/255).
    image_shape : tuple
        Shape of the image that produced ``mask`` (height, width, …).
    config : dict
        Project configuration.  Reads the optional ``candidate`` section.

    Returns
    -------
    is_valid : bool
    reason : str
        Empty string when valid; human-readable explanation otherwise.
    """
    cfg = dict(_DEFAULT_CANDIDATE)
    user_cfg = config.get("candidate", {})
    if user_cfg:
        cfg.update(user_cfg)

    image_h, image_w = int(image_shape[0]), int(image_shape[1])
    image_area = image_h * image_w

    # ---- 1. mask area ratio ---------------------------------------------
    mask_area = int(features.get("mask_area", 0))
    area_ratio = mask_area / max(image_area, 1)

    min_area = float(cfg["min_area_ratio"])
    max_area = float(cfg["max_area_ratio"])

    if area_ratio < min_area:
        return False, f"分割区域过小 (面积比 {area_ratio:.4f} < {min_area})"
    if area_ratio > max_area:
        return False, f"分割区域过大 (面积比 {area_ratio:.4f} > {max_area})"

    # ---- 2. rotated bounding-box aspect ratio ---------------------------
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, "无有效轮廓"

    all_points = np.vstack(contours)
    rot_rect = cv2.minAreaRect(all_points)
    (rw, rh) = rot_rect[1]
    if rw <= 0 or rh <= 0:
        return False, "旋转边界框尺寸无效"

    long_side = float(max(rw, rh))
    short_side = float(min(rw, rh))
    rotated_aspect = long_side / max(short_side, 1.0)

    min_aspect = float(cfg["min_rotated_aspect"])
    max_aspect = float(cfg["max_rotated_aspect"])

    if rotated_aspect < min_aspect:
        return False, f"边界框过于方正 (旋转长宽比 {rotated_aspect:.1f} < {min_aspect})"
    if rotated_aspect > max_aspect:
        return False, f"边界框过于细长 (旋转长宽比 {rotated_aspect:.1f} > {max_aspect})"

    # ---- 3. extent (fill ratio of rotated rect) -------------------------
    rect_area = rw * rh
    extent = mask_area / max(rect_area, 1.0)
    min_extent = float(cfg["min_extent"])

    if extent < min_extent:
        return False, f"填充度过低 (extent {extent:.3f} < {min_extent})"

    # ---- 4. banana colour ratio (green + yellow + brown) ----------------
    banana_color = float(features.get("banana_color_ratio", 0.0))
    min_color = float(cfg["min_banana_color_ratio"])

    if banana_color < min_color:
        return False, (
            f"香蕉颜色占比过低 "
            f"(green+yellow+brown={banana_color:.3f} < {min_color})"
        )

    # ---- 5. yellow-green ratio (green + yellow) -------------------------
    yg_ratio = float(features.get("yellow_green_ratio", 0.0))
    min_yg = float(cfg["min_yellow_green_ratio"])

    if yg_ratio < min_yg:
        return False, (
            f"黄绿色占比过低 (green+yellow={yg_ratio:.3f} < {min_yg})"
        )

    # ---- 6. dark-ratio veto ---------------------------------------------
    dark = float(features.get("dark_ratio", 0.0))
    max_dark = float(cfg["max_dark_ratio_for_presence"])

    if dark > max_dark:
        return False, (
            f"暗色占比过高 (dark_ratio={dark:.3f} > {max_dark})"
        )

    # ---- 7. center ROI --------------------------------------------------
    use_roi = bool(cfg.get("use_center_roi", True))
    if use_roi:
        roi_w = float(cfg.get("roi_width_ratio", 0.70))
        roi_h = float(cfg.get("roi_height_ratio", 0.70))

        # ROI bounds (inclusive on the inside)
        roi_left = int(image_w * (1.0 - roi_w) / 2.0)
        roi_right = int(image_w * (1.0 + roi_w) / 2.0)
        roi_top = int(image_h * (1.0 - roi_h) / 2.0)
        roi_bottom = int(image_h * (1.0 + roi_h) / 2.0)

        # Mask centre of mass
        moments = cv2.moments(mask)
        if moments["m00"] > 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
        else:
            cx, cy = image_w // 2, image_h // 2

        if not (roi_left <= cx <= roi_right and roi_top <= cy <= roi_bottom):
            return False, (
                f"目标不在画面中心区域 (重心=({cx},{cy}), "
                f"ROI=({roi_left},{roi_top})-({roi_right},{roi_bottom}))"
            )

    return True, ""


# ---------------------------------------------------------------------------
# Convenience: full pipeline in one call
# ---------------------------------------------------------------------------


def run_inference_on_frame(
    frame_bgr: np.ndarray,
    config: dict[str, Any],
    method: str,
    model_cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the complete inference pipeline on a single camera frame.

    Convenience wrapper that chains :func:`extract_features_for_frame`,
    :func:`is_valid_banana_candidate`, and :func:`predict_features`.

    Returns a dictionary with keys:

    * ``prediction`` — class label (``"unknown"`` when candidate check fails)
    * ``proba`` — class probability dict
    * ``method_used`` — actual method identifier (may reflect fallback)
    * ``features`` — full feature dict
    * ``processed`` — preprocessed BGR image
    * ``mask`` — binary segmentation mask
    * ``banana_detected`` — bool
    * ``candidate_reason`` — str, empty if banana detected
    """
    features, processed, mask = extract_features_for_frame(frame_bgr, config)

    banana_detected, reason = is_valid_banana_candidate(
        features, mask, processed.shape, config,
    )

    if not banana_detected:
        return {
            "prediction": "unknown",
            "proba": {},
            "method_used": "规则分类（未检测到香蕉）",
            "features": features,
            "processed": processed,
            "mask": mask,
            "banana_detected": False,
            "candidate_reason": reason,
        }

    prediction, proba, method_used = predict_features(
        features, config, method, model_cache,
    )
    return {
        "prediction": prediction,
        "proba": proba,
        "method_used": method_used,
        "features": features,
        "processed": processed,
        "mask": mask,
        "banana_detected": True,
        "candidate_reason": "",
    }
