from __future__ import annotations

import cv2
import numpy as np


def clean_mask(mask: np.ndarray, kernel_size: int = 7) -> np.ndarray:
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def largest_connected_component(mask: np.ndarray, min_area: int = 0) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 1:
        return np.zeros_like(mask, dtype=np.uint8)

    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_index = int(np.argmax(areas)) + 1
    if int(stats[largest_index, cv2.CC_STAT_AREA]) < min_area:
        return np.zeros_like(mask, dtype=np.uint8)

    result = np.zeros_like(mask, dtype=np.uint8)
    result[labels == largest_index] = 255
    return result


def mask_bounding_box(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    points = cv2.findNonZero((mask > 0).astype(np.uint8))
    if points is None:
        return None
    x, y, w, h = cv2.boundingRect(points)
    return x, y, w, h
