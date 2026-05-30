from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .feature_glcm import extract_glcm_features
from .feature_hsv import extract_hsv_features
from .preprocessing import preprocess_image
from .rule_classifier import classify_by_rules
from .segmentation import segment_banana
from .utils import infer_label, list_image_files, merge_dicts, read_image


FEATURE_COLUMNS = [
    "green_ratio",
    "yellow_ratio",
    "dark_ratio",
    "H_mean",
    "H_std",
    "S_mean",
    "S_std",
    "V_mean",
    "V_std",
    "glcm_contrast",
    "glcm_energy",
    "glcm_homogeneity",
    "glcm_correlation",
]


def extract_features_for_image(image_path: str | Path, config: dict[str, Any]) -> tuple[dict[str, Any], Any, Any]:
    image = read_image(image_path)
    prep_cfg = config.get("preprocessing", {})
    processed = preprocess_image(
        image,
        max_size=int(prep_cfg.get("max_size", 900)),
        blur_kernel=int(prep_cfg.get("blur_kernel", 5)),
    )

    seg_cfg = config.get("segmentation", {})
    mask, _ = segment_banana(
        processed,
        min_area_ratio=float(seg_cfg.get("min_area_ratio", 0.01)),
        morphology_kernel=int(seg_cfg.get("morphology_kernel", 7)),
    )

    feat_cfg = config.get("features", {})
    hsv_features = extract_hsv_features(processed, mask)
    glcm_features = extract_glcm_features(
        processed,
        mask,
        levels=int(feat_cfg.get("glcm_levels", 32)),
        distances=feat_cfg.get("glcm_distances", [1, 2]),
    )
    features = merge_dicts(hsv_features, glcm_features)
    prediction = classify_by_rules(features, config.get("rules", {}))

    row = {
        "image_path": str(Path(image_path)),
        "label": infer_label(image_path),
        **features,
        "rule_prediction": prediction,
        "mask_area": int((mask > 0).sum()),
    }
    return row, processed, mask


def build_feature_table(input_path: str | Path, config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for image_path in list_image_files(input_path):
        row, _, _ = extract_features_for_image(image_path, config)
        rows.append(row)
    return pd.DataFrame(rows)
