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
    """CLAHE on L-channel in LAB space — corrects uneven illumination."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def simple_white_balance(
    image_bgr: np.ndarray,
    percentile: float = 1.0,
) -> np.ndarray:
    """Stretch each BGR channel independently to [0, 255] using percentiles.

    A lightweight colour-constancy correction that reduces the impact of
    warm (incandescent) or cool (LED / fluorescent) ambient light on HSV
    segmentation.  Channels are clipped at *percentile* and
    *(100 − percentile)* then linearly mapped to full range.

    Parameters
    ----------
    image_bgr : np.ndarray
        Input BGR image (uint8).
    percentile : float
        Percentile for clipping (default 1.0 — clips 1 % darkest and
        1 % brightest pixels per channel).

    Returns
    -------
    np.ndarray
        White-balanced BGR image (uint8, same shape).
    """
    img_float = image_bgr.astype(np.float32)
    b, g, r = cv2.split(img_float)

    b_low, b_high = np.percentile(b, percentile), np.percentile(b, 100.0 - percentile)
    g_low, g_high = np.percentile(g, percentile), np.percentile(g, 100.0 - percentile)
    r_low, r_high = np.percentile(r, percentile), np.percentile(r, 100.0 - percentile)

    def _stretch(ch: np.ndarray, lo: float, hi: float) -> np.ndarray:
        denom = max(hi - lo, 1.0)
        return np.clip((ch - lo) * 255.0 / denom, 0, 255)

    b = _stretch(b, b_low, b_high)
    g = _stretch(g, g_low, g_high)
    r = _stretch(r, r_low, r_high)

    return cv2.merge([b, g, r]).astype(np.uint8)


def preprocess_image(
    image: np.ndarray,
    max_size: int = 900,
    blur_kernel: int = 5,
    equalize: bool = True,
    white_balance: bool = False,
    wb_percentile: float = 1.0,
) -> np.ndarray:
    """Full preprocessing pipeline.

    Parameters
    ----------
    white_balance : bool
        Apply :func:`simple_white_balance` before equalisation.
        Recommended for camera real-time mode to reduce ambient-light
        colour shifts.
    wb_percentile : float
        Percentile for white-balance clipping (only used when
        *white_balance* is True).
    """
    processed = resize_max_side(image, max_size=max_size)

    # White balance BEFORE blur + CLAHE — corrects colour casts first.
    if white_balance:
        processed = simple_white_balance(processed, percentile=wb_percentile)

    if blur_kernel and blur_kernel > 1:
        if blur_kernel % 2 == 0:
            blur_kernel += 1
        processed = cv2.GaussianBlur(processed, (blur_kernel, blur_kernel), 0)
    if equalize:
        processed = normalize_lighting(processed)
    return processed
