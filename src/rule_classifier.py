from __future__ import annotations

from typing import Any


DEFAULT_RULES = {
    "green_ratio_threshold": 0.32,
    "dark_ratio_threshold": 0.18,
    "contrast_threshold": 35.0,
    "yellow_ratio_threshold": 0.45,
}


def classify_by_rules(features: dict[str, float], rules: dict[str, Any] | None = None) -> str:
    config = dict(DEFAULT_RULES)
    if rules:
        config.update(rules)

    green_ratio = float(features.get("green_ratio", 0.0))
    yellow_ratio = float(features.get("yellow_ratio", 0.0))
    dark_ratio = float(features.get("dark_ratio", 0.0))
    contrast = float(features.get("glcm_contrast", 0.0))

    if green_ratio >= float(config["green_ratio_threshold"]):
        return "unripe"
    if dark_ratio >= float(config["dark_ratio_threshold"]):
        return "overripe"
    if contrast >= float(config["contrast_threshold"]) and dark_ratio >= 0.08:
        return "overripe"
    if yellow_ratio >= float(config["yellow_ratio_threshold"]):
        return "ripe"
    return "ripe"
