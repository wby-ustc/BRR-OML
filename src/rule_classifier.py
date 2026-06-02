from __future__ import annotations

from typing import Any


DEFAULT_RULES = {
    "green_ratio_threshold": 0.012,
    "dark_ratio_threshold": 0.40,
    "contrast_threshold": 1.45,
    "yellow_ratio_threshold": 0.50,
    "dark_ratio_low": 0.32,
    "overripe_yellow_max": 0.55,
    "contrast_high": 1.70,
}


def classify_by_rules(features: dict[str, float], rules: dict[str, Any] | None = None) -> str:
    """Classify banana ripeness using configurable rule-based thresholds.

    Rules are evaluated in priority order:
      1. green_ratio >= green_ratio_threshold -> unripe
      2. dark_ratio >= dark_ratio_threshold
         AND yellow_ratio <= overripe_yellow_max -> overripe (colour-based)
      3. glcm_contrast >= contrast_high -> overripe (texture-dominant,
         added 2026-06-01 for overripe samples with low dark_ratio but
         high texture contrast from brown spots / surface decay)
      4. glcm_contrast >= contrast_threshold
         AND dark_ratio >= dark_ratio_low -> overripe (texture+dark combo,
         safety net for overripe with moderate contrast)
      5. yellow_ratio >= yellow_ratio_threshold -> ripe
      6. fallback -> ripe
    """
    config = dict(DEFAULT_RULES)
    if rules:
        config.update(rules)

    green_ratio = float(features.get("green_ratio", 0.0))
    yellow_ratio = float(features.get("yellow_ratio", 0.0))
    dark_ratio = float(features.get("dark_ratio", 0.0))
    contrast = float(features.get("glcm_contrast", 0.0))

    green_th = float(config["green_ratio_threshold"])
    dark_th = float(config["dark_ratio_threshold"])
    contrast_th = float(config["contrast_threshold"])
    contrast_high = float(config.get("contrast_high", 1.70))
    yellow_th = float(config["yellow_ratio_threshold"])
    dark_low = float(config.get("dark_ratio_low", 0.32))
    overripe_yellow_max = float(config.get("overripe_yellow_max", 0.55))

    # Rule 1: high green ratio -> unripe
    if green_ratio >= green_th:
        return "unripe"

    # Rule 2: high dark ratio combined with low yellow -> overripe
    if dark_ratio >= dark_th and yellow_ratio <= overripe_yellow_max:
        return "overripe"

    # Rule 3: high texture contrast -> overripe
    # (captures overripe with brown spots / surface decay independent of dark_ratio)
    if contrast >= contrast_high:
        return "overripe"

    # Rule 4: texture contrast + moderate dark -> overripe (safety net)
    if contrast >= contrast_th and dark_ratio >= dark_low:
        return "overripe"

    # Rule 5: dominant yellow -> ripe
    if yellow_ratio >= yellow_th:
        return "ripe"

    # Rule 6: fallback
    return "ripe"
