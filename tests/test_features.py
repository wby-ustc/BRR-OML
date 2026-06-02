"""Unit tests for HSV feature extraction, GLCM feature extraction, and rule classifier."""

import numpy as np

from src.feature_glcm import extract_glcm_features
from src.feature_hsv import extract_hsv_features
from src.rule_classifier import DEFAULT_RULES, classify_by_rules


# ---------------------------------------------------------------------------
# HSV feature extraction
# ---------------------------------------------------------------------------


def test_hsv_features_detect_green_region():
    """Pure green image should yield green_ratio > 0.9 and yellow_ratio < 0.1."""
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:] = (0, 180, 0)  # BGR green
    mask = np.ones((40, 40), dtype=np.uint8) * 255

    features = extract_hsv_features(image, mask)

    assert features["green_ratio"] > 0.9
    assert features["yellow_ratio"] < 0.1


def test_hsv_features_detect_yellow_region():
    """Pure yellow image should yield yellow_ratio > 0.9."""
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:] = (0, 235, 235)  # BGR yellow
    mask = np.ones((40, 40), dtype=np.uint8) * 255

    features = extract_hsv_features(image, mask)

    assert features["yellow_ratio"] > 0.9
    assert features["green_ratio"] < 0.1


def test_hsv_features_empty_mask():
    """Empty mask should return zero ratios and zero stats."""
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:] = (0, 180, 0)
    mask = np.zeros((40, 40), dtype=np.uint8)

    features = extract_hsv_features(image, mask)

    assert features["green_ratio"] == 0.0
    assert features["yellow_ratio"] == 0.0
    assert features["dark_ratio"] == 0.0
    assert features["H_mean"] == 0.0
    assert features["S_mean"] == 0.0
    assert features["V_mean"] == 0.0


def test_hsv_features_output_keys():
    """Check that all expected feature keys are present."""
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:] = (0, 200, 200)
    mask = np.ones((40, 40), dtype=np.uint8) * 255

    features = extract_hsv_features(image, mask)

    expected_keys = {
        "green_ratio",
        "yellow_ratio",
        "dark_ratio",
        "H_mean",
        "H_std",
        "S_mean",
        "S_std",
        "V_mean",
        "V_std",
    }
    assert expected_keys.issubset(set(features.keys()))


# ---------------------------------------------------------------------------
# GLCM feature extraction
# ---------------------------------------------------------------------------


def test_glcm_empty_mask_returns_zeros():
    """Empty mask should return zero for all GLCM features."""
    image = np.random.randint(0, 255, (80, 80, 3), dtype=np.uint8)
    mask = np.zeros((80, 80), dtype=np.uint8)

    features = extract_glcm_features(image, mask)

    for key in ("glcm_contrast", "glcm_energy", "glcm_homogeneity", "glcm_correlation"):
        assert features[key] == 0.0, f"{key} should be 0.0 for empty mask"


def test_glcm_output_keys():
    """Check that all four GLCM keys are present."""
    image = np.random.randint(0, 255, (80, 80, 3), dtype=np.uint8)
    mask = np.ones((80, 80), dtype=np.uint8) * 255

    features = extract_glcm_features(image, mask)

    for key in ("glcm_contrast", "glcm_energy", "glcm_homogeneity", "glcm_correlation"):
        assert key in features, f"{key} should be in GLCM features"


def test_glcm_constant_region():
    """A constant-color region should have near-zero contrast and high homogeneity."""
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    image[:] = (0, 200, 200)
    mask = np.ones((64, 64), dtype=np.uint8) * 255

    features = extract_glcm_features(image, mask)

    # A perfectly uniform region: contrast ~= 0, homogeneity ~= 1.
    assert features["glcm_contrast"] < 0.1
    assert features["glcm_homogeneity"] > 0.9
    assert features["glcm_energy"] > 0.0


def test_glcm_small_roi():
    """Very small valid region (< 16 px) should return zeros."""
    image = np.random.randint(0, 255, (40, 40, 3), dtype=np.uint8)
    mask = np.zeros((40, 40), dtype=np.uint8)
    mask[10:13, 10:13] = 255  # only 9 foreground pixels

    features = extract_glcm_features(image, mask)

    for key in ("glcm_contrast", "glcm_energy", "glcm_homogeneity", "glcm_correlation"):
        assert features[key] == 0.0, f"{key} should be 0.0 for tiny valid region"


# ---------------------------------------------------------------------------
# Rule classifier
# ---------------------------------------------------------------------------


def test_rule_classifier_prefers_unripe_for_green_ratio():
    features = {
        "green_ratio": 0.5,
        "yellow_ratio": 0.2,
        "dark_ratio": 0.0,
        "glcm_contrast": 2.0,
    }
    assert classify_by_rules(features) == "unripe"


def test_rule_classifier_returns_ripe_for_yellow():
    """A clearly yellow banana with low dark ratio should be ripe."""
    features = {
        "green_ratio": 0.01,
        "yellow_ratio": 0.8,
        "dark_ratio": 0.05,
        "glcm_contrast": 0.5,
    }
    assert classify_by_rules(features) == "ripe"


def test_rule_classifier_overripe_combined_rule():
    """High dark + low yellow -> overripe."""
    features = {
        "green_ratio": 0.01,
        "yellow_ratio": 0.35,
        "dark_ratio": 0.50,
        "glcm_contrast": 0.5,
    }
    assert classify_by_rules(features) == "overripe"


def test_rule_classifier_overripe_contrast_rule():
    """High contrast + moderate dark -> overripe."""
    features = {
        "green_ratio": 0.01,
        "yellow_ratio": 0.70,
        "dark_ratio": 0.35,
        "glcm_contrast": 2.0,
    }
    assert classify_by_rules(features) == "overripe"


def test_rule_classifier_high_dark_but_high_yellow_is_ripe():
    """High dark ratio but also high yellow -> still ripe."""
    features = {
        "green_ratio": 0.01,
        "yellow_ratio": 0.75,
        "dark_ratio": 0.55,
        "glcm_contrast": 0.3,
    }
    assert classify_by_rules(features) == "ripe"


def test_rule_classifier_custom_thresholds():
    """Custom thresholds should override defaults."""
    features = {
        "green_ratio": 0.15,
        "yellow_ratio": 0.1,
        "dark_ratio": 0.1,
        "glcm_contrast": 1.0,
    }

    custom = {"green_ratio_threshold": 0.10}
    assert classify_by_rules(features, rules=custom) == "unripe"
    # With updated DEFAULT_RULES (green_ratio_threshold=0.012), gr=0.15 -> unripe
    assert classify_by_rules(features) == "unripe"


def test_rule_classifier_default_rules_complete():
    """DEFAULT_RULES dict should contain all required keys."""
    required = {
        "green_ratio_threshold",
        "dark_ratio_threshold",
        "contrast_threshold",
        "yellow_ratio_threshold",
        "dark_ratio_low",
        "overripe_yellow_max",
        "contrast_high",
    }
    assert required.issubset(set(DEFAULT_RULES.keys()))


def test_rule_classifier_contrast_high_triggers_overripe():
    """High contrast alone (>= contrast_high) should trigger overripe even with low dark_ratio."""
    features = {
        "green_ratio": 0.001,
        "yellow_ratio": 0.80,
        "dark_ratio": 0.25,
        "glcm_contrast": 2.5,
    }
    # green_ratio below threshold -> skip R1
    # dark_ratio < 0.40 -> skip R2
    # contrast 2.5 >= contrast_high 1.70 -> R3 triggers overripe
    assert classify_by_rules(features) == "overripe"


def test_rule_classifier_contrast_high_respects_priority():
    """Rule 1 (green_ratio) takes priority over Rule 3 (contrast_high)."""
    features = {
        "green_ratio": 0.50,
        "yellow_ratio": 0.30,
        "dark_ratio": 0.10,
        "glcm_contrast": 3.0,
    }
    # green_ratio 0.50 >= 0.012 -> R1 triggers unripe (even though contrast is very high)
    assert classify_by_rules(features) == "unripe"
