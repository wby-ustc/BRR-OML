from __future__ import annotations

import cv2
import numpy as np

from .morphology import clean_mask, largest_connected_component


def hsv_color_masks(image_bgr: np.ndarray) -> dict[str, np.ndarray]:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    green = cv2.inRange(hsv, np.array([35, 35, 35]), np.array([90, 255, 255]))
    yellow = cv2.inRange(hsv, np.array([15, 35, 45]), np.array([38, 255, 255]))
    brown = cv2.inRange(hsv, np.array([5, 35, 20]), np.array([25, 255, 170]))

    h, s, v = cv2.split(hsv)
    dark = np.zeros_like(v, dtype=np.uint8)
    dark[((v < 80) & (s > 25)) | ((h >= 0) & (h <= 25) & (v < 125) & (s > 35))] = 255

    return {
        "green": green,
        "yellow": yellow,
        "brown": brown,
        "dark": dark,
    }


def segment_banana(
    image_bgr: np.ndarray,
    min_area_ratio: float = 0.01,
    morphology_kernel: int = 7,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    masks = hsv_color_masks(image_bgr)
    candidate = cv2.bitwise_or(masks["green"], masks["yellow"])
    candidate = cv2.bitwise_or(candidate, masks["brown"])
    candidate = cv2.bitwise_or(candidate, masks["dark"])
    candidate = clean_mask(candidate, kernel_size=morphology_kernel)

    min_area = int(image_bgr.shape[0] * image_bgr.shape[1] * min_area_ratio)
    banana_mask = largest_connected_component(candidate, min_area=min_area)
    return banana_mask, masks
