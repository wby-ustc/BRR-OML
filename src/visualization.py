from __future__ import annotations

import cv2
import numpy as np


LABEL_COLORS = {
    "unripe": (60, 180, 60),
    "ripe": (0, 210, 255),
    "overripe": (30, 80, 150),
    "unknown": (220, 220, 220),
}


def overlay_mask(image_bgr: np.ndarray, mask: np.ndarray, color: tuple[int, int, int] = (0, 255, 255)) -> np.ndarray:
    overlay = image_bgr.copy()
    color_layer = np.zeros_like(image_bgr)
    color_layer[:] = color
    mask_bool = mask > 0
    overlay[mask_bool] = cv2.addWeighted(image_bgr, 0.65, color_layer, 0.35, 0)[mask_bool]
    return overlay


def draw_prediction(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    prediction: str,
    confidence_text: str = "",
) -> np.ndarray:
    label = prediction or "unknown"
    color = LABEL_COLORS.get(label, LABEL_COLORS["unknown"])
    canvas = overlay_mask(image_bgr, mask, color=color)

    text = f"Prediction: {label}"
    if confidence_text:
        text = f"{text} | {confidence_text}"
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 48), (0, 0, 0), thickness=-1)
    cv2.putText(canvas, text, (16, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    return canvas


def make_side_by_side(original: np.ndarray, mask: np.ndarray, annotated: np.ndarray) -> np.ndarray:
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    target_size = (original.shape[1], original.shape[0])
    if annotated.shape[:2] != original.shape[:2]:
        annotated = cv2.resize(annotated, target_size)
    return np.hstack([original, mask_bgr, annotated])
