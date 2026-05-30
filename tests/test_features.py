import numpy as np

from src.feature_hsv import extract_hsv_features
from src.rule_classifier import classify_by_rules


def test_hsv_features_detect_green_region():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:] = (0, 180, 0)
    mask = np.ones((40, 40), dtype=np.uint8) * 255

    features = extract_hsv_features(image, mask)

    assert features["green_ratio"] > 0.9
    assert features["yellow_ratio"] < 0.1


def test_rule_classifier_prefers_unripe_for_green_ratio():
    features = {
        "green_ratio": 0.5,
        "yellow_ratio": 0.2,
        "dark_ratio": 0.0,
        "glcm_contrast": 2.0,
    }

    assert classify_by_rules(features) == "unripe"
