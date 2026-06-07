from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .dataset_builder import FEATURE_COLUMNS

CLASSES = ["unripe", "ripe", "overripe"]
REQUIRED_CLASSES: set[str] = {"unripe", "ripe", "overripe"}


def load_feature_data(
    csv_path: str | Path,
    *,
    allow_single_class: bool = True,
) -> tuple[pd.DataFrame, pd.Series]:
    """Load labeled feature rows from a combined_features.csv.

    Returns (X, y).  If ``allow_single_class`` is False and fewer than 2
    classes are present a ValueError is raised.
    """
    df = pd.read_csv(csv_path)
    labeled = df[df["label"].notna() & (df["label"].astype(str).str.strip() != "")]
    if labeled.empty:
        raise ValueError(
            "No labeled rows found. Place images under data/raw/unripe, ripe, overripe "
            "and re-run: python -m src.main_rule_based"
        )

    classes_present = set(labeled["label"].unique())
    if not allow_single_class and len(classes_present) < 2:
        raise ValueError(
            f"Only {len(classes_present)} class(es) found: {sorted(classes_present)}. "
            "At least 2 classes are required for supervised training."
        )

    missing = [c for c in FEATURE_COLUMNS if c not in labeled.columns]
    if missing:
        raise KeyError(f"Missing feature columns in CSV: {missing}")

    return labeled[FEATURE_COLUMNS].astype(float), labeled["label"].astype(str)


def make_knn(k: int = 5) -> Pipeline:
    """K-Nearest Neighbors with feature standardization."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", KNeighborsClassifier(n_neighbors=k)),
        ]
    )


def make_svm(kernel: str = "rbf", C: float = 10.0) -> Pipeline:
    """RBF-kernel SVM with feature standardization."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", SVC(kernel=kernel, C=C, gamma="scale", probability=True)),
        ]
    )


def make_logistic(C: float = 1.0, max_iter: int = 2000) -> Pipeline:
    """L2-regularised logistic regression baseline.

    Uses ``auto`` multi_class so it works across scikit-learn versions.
    """
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(C=C, max_iter=max_iter),
            ),
        ]
    )


def save_model(model: Pipeline, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(Path(path))


def predict_single(model: Pipeline, features: dict[str, float]) -> tuple[str, dict[str, float]]:
    """Predict a single sample from a feature dict.

    Returns (predicted_label, {class_name: probability}).
    """
    ordered = np.array([[features.get(c, 0.0) for c in FEATURE_COLUMNS]], dtype=float)
    pred = model.predict(ordered)[0]
    try:
        proba = model.predict_proba(ordered)[0]
        proba_dict = {str(cls): float(p) for cls, p in zip(model.classes_, proba)}
    except AttributeError:
        proba_dict = {}
    return str(pred), proba_dict


def get_model_info(model: Pipeline) -> dict[str, Any]:
    """Return a summary dict describing the trained model."""
    info: dict[str, Any] = {"steps": [step[0] for step in model.steps]}
    if hasattr(model, "classes_"):
        info["classes"] = list(model.classes_)
    clf = model.named_steps.get("classifier")
    if clf is not None:
        info["classifier_type"] = type(clf).__name__
        if hasattr(clf, "get_params"):
            info["params"] = {k: v for k, v in clf.get_params().items() if not k.startswith("_")}
    return info


# ---------------------------------------------------------------------------
# Model validation — prevents single-class debug models from being used
# ---------------------------------------------------------------------------


def validate_model_classes(
    model: Pipeline,
    required_classes: set[str] | None = None,
) -> tuple[bool, str]:
    """Check that a trained model covers all required ripeness classes.

    A single-class model (e.g. trained with ``--allow-single-class``) will
    always predict that one class with 100 % confidence, which is misleading.
    This function gates model usage on having the full label set.

    Parameters
    ----------
    model : Pipeline
        Fitted scikit-learn pipeline.
    required_classes : set[str] or None
        Required labels.  Defaults to ``{"unripe", "ripe", "overripe"}``.

    Returns
    -------
    valid : bool
    reason : str
        Human-readable explanation (empty if valid).
    """
    required = required_classes or REQUIRED_CLASSES

    if not hasattr(model, "classes_"):
        return False, "模型未训练（缺少 classes_ 属性）"

    model_classes = set(str(c) for c in model.classes_)
    if model_classes != required:
        missing = required - model_classes
        extra = model_classes - required
        parts = []
        if missing:
            parts.append(f"缺少类别: {sorted(missing)}")
        if extra:
            parts.append(f"多余类别: {sorted(extra)}")
        return False, (
            f"模型类别不完整（当前: {sorted(model_classes)}，需要: {sorted(required)}）；"
            + "；".join(parts)
        )

    return True, ""


# ---------------------------------------------------------------------------
# Model metadata (saved alongside the .pkl file for runtime checks)
# ---------------------------------------------------------------------------

_META_SUFFIX = "_meta.json"


def save_model_meta(model_path: str | Path, meta: dict[str, Any]) -> Path:
    """Save a model metadata JSON next to the model file.

    Example: ``knn_model.pkl`` → ``knn_model_meta.json``.
    """
    pkl_path = Path(model_path)
    meta_path = pkl_path.with_name(pkl_path.stem + _META_SUFFIX)
    serializable: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool, list, dict, type(None))):
            serializable[k] = v
        else:
            serializable[k] = str(v)
    meta_path.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return meta_path


def load_model_meta(model_path: str | Path) -> dict[str, Any] | None:
    """Load model metadata JSON if it exists; return ``None`` otherwise."""
    pkl_path = Path(model_path)
    meta_path = pkl_path.with_name(pkl_path.stem + _META_SUFFIX)
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
