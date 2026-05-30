from __future__ import annotations

import cv2
import numpy as np

from .segmentation import hsv_color_masks


def _ratio(color_mask: np.ndarray, banana_mask: np.ndarray, total: int) -> float:
    if total <= 0:
        return 0.0
    overlap = cv2.bitwise_and(color_mask, color_mask, mask=banana_mask)
    return float(np.count_nonzero(overlap)) / float(total)


def extract_hsv_features(image_bgr: np.ndarray, banana_mask: np.ndarray) -> dict[str, float]:
    mask = (banana_mask > 0).astype(np.uint8) * 255
    total = int(np.count_nonzero(mask))
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    color_masks = hsv_color_masks(image_bgr)

    features = {
        "green_ratio": _ratio(color_masks["green"], mask, total),
        "yellow_ratio": _ratio(color_masks["yellow"], mask, total),
        "dark_ratio": _ratio(color_masks["dark"], mask, total),
    }

    if total == 0:
        features.update(
            {
                "H_mean": 0.0,
                "H_std": 0.0,
                "S_mean": 0.0,
                "S_std": 0.0,
                "V_mean": 0.0,
                "V_std": 0.0,
            }
        )
        return features

    pixels = hsv[mask > 0]
    channel_names = ["H", "S", "V"]
    for index, name in enumerate(channel_names):
        values = pixels[:, index].astype(np.float32)
        features[f"{name}_mean"] = float(np.mean(values))
        features[f"{name}_std"] = float(np.std(values))
    return features
