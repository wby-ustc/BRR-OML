from __future__ import annotations

import cv2
import numpy as np


def resize_max_side(image: np.ndarray, max_size: int = 900) -> np.ndarray:
    if max_size <= 0:
        return image
    height, width = image.shape[:2]
    scale = max(height, width) / float(max_size)
    if scale <= 1.0:
        return image
    new_size = (int(width / scale), int(height / scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def normalize_lighting(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def preprocess_image(
    image: np.ndarray,
    max_size: int = 900,
    blur_kernel: int = 5,
    equalize: bool = True,
) -> np.ndarray:
    processed = resize_max_side(image, max_size=max_size)
    if blur_kernel and blur_kernel > 1:
        if blur_kernel % 2 == 0:
            blur_kernel += 1
        processed = cv2.GaussianBlur(processed, (blur_kernel, blur_kernel), 0)
    if equalize:
        processed = normalize_lighting(processed)
    return processed
