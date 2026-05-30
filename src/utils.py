from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
import yaml


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
LABELS = {"unripe", "ripe", "overripe"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return (base or project_root()) / path


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config(config_path: str | Path = "config.yaml") -> dict[str, Any]:
    path = resolve_path(config_path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_image_files(path: str | Path) -> list[Path]:
    path = resolve_path(path)
    if path.is_file():
        return [path] if path.suffix.lower() in IMAGE_EXTENSIONS else []
    files: list[Path] = []
    for item in path.rglob("*"):
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(item)
    return sorted(files)


def infer_label(image_path: str | Path) -> str:
    parts = {part.lower() for part in Path(image_path).parts}
    for label in LABELS:
        if label in parts:
            return label
    return ""


def safe_stem(path: str | Path) -> str:
    path = Path(path)
    parent = path.parent.name if path.parent.name else "image"
    return f"{parent}_{path.stem}"


def read_image(path: str | Path) -> np.ndarray:
    path = Path(path)
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def write_image(path: str | Path, image: np.ndarray) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    ext = path.suffix or ".png"
    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        raise ValueError(f"Unable to encode image for: {path}")
    encoded.tofile(str(path))


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for data in dicts:
        merged.update(data)
    return merged


def format_float_dict(data: dict[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    formatted = dict(data)
    for key in keys:
        if key in formatted:
            formatted[key] = float(formatted[key])
    return formatted
