from __future__ import annotations

import cv2
import numpy as np

from .morphology import mask_bounding_box

try:
    from skimage.feature import graycomatrix, graycoprops
except ImportError:  # pragma: no cover - compatibility with older scikit-image
    from skimage.feature import greycomatrix as graycomatrix
    from skimage.feature import greycoprops as graycoprops


GLCM_KEYS = ["contrast", "energy", "homogeneity", "correlation"]


def _empty_features() -> dict[str, float]:
    return {f"glcm_{key}": 0.0 for key in GLCM_KEYS}


def extract_glcm_features(
    image_bgr: np.ndarray,
    banana_mask: np.ndarray,
    levels: int = 32,
    distances: list[int] | tuple[int, ...] = (1, 2),
) -> dict[str, float]:
    bbox = mask_bounding_box(banana_mask)
    if bbox is None:
        return _empty_features()

    x, y, w, h = bbox
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)[y : y + h, x : x + w]
    mask = banana_mask[y : y + h, x : x + w] > 0
    if np.count_nonzero(mask) < 16:
        return _empty_features()

    masked_values = gray[mask]
    fill_value = int(np.median(masked_values))
    roi = gray.copy()
    roi[~mask] = fill_value

    levels = max(8, int(levels))
    quantized = np.floor(roi.astype(np.float32) / 256.0 * levels).astype(np.uint8)
    quantized = np.clip(quantized, 0, levels - 1)

    glcm = graycomatrix(
        quantized,
        distances=list(distances),
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=levels,
        symmetric=True,
        normed=True,
    )

    return {
        "glcm_contrast": float(np.mean(graycoprops(glcm, "contrast"))),
        "glcm_energy": float(np.mean(graycoprops(glcm, "energy"))),
        "glcm_homogeneity": float(np.mean(graycoprops(glcm, "homogeneity"))),
        "glcm_correlation": float(np.mean(graycoprops(glcm, "correlation"))),
    }
