from __future__ import annotations

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
