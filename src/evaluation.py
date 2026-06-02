from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline

from .dataset_builder import FEATURE_COLUMNS


# ---------------------------------------------------------------------------
# Report / matrix persistence
# ---------------------------------------------------------------------------


def save_classification_report(y_true, y_pred, path: str | Path) -> str:
    """Save a text classification report and return the report string."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = classification_report(y_true, y_pred, zero_division=0)
    path.write_text(report, encoding="utf-8")
    return report


def save_confusion_matrix(
    y_true,
    y_pred,
    path: str | Path,
    labels: list[str] | None = None,
    title: str = "Confusion Matrix",
) -> None:
    """Save a confusion-matrix figure to *path*."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, labels=labels, xticks_rotation=45
    )
    display.ax_.set_title(title)
    display.figure_.tight_layout()
    display.figure_.savefig(path, dpi=160)
    plt.close(display.figure_)


# ---------------------------------------------------------------------------
# Cross-validation evaluation
# ---------------------------------------------------------------------------


def evaluate_cross_validation(
    model: Pipeline,
    x: pd.DataFrame,
    y: pd.Series,
    *,
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run stratified k-fold cross-validation.

    Returns a dict with keys:
      - ``cv_accuracy_mean``, ``cv_accuracy_std``
      - ``cv_fold_accuracies`` (list of per-fold accuracy)
      - ``cv_predictions`` (cross_val_predict outputs)
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    # When fewer samples than splits for a class, reduce splits
    min_count = y.value_counts().min()
    effective_splits = min(n_splits, min_count, len(y))
    if effective_splits < 2:
        return {
            "cv_accuracy_mean": float("nan"),
            "cv_accuracy_std": float("nan"),
            "cv_fold_accuracies": [],
            "cv_predictions": np.array([]),
            "warning": f"Insufficient samples for CV (min class count={min_count})",
        }

    if effective_splits < n_splits:
        skf = StratifiedKFold(n_splits=effective_splits, shuffle=True, random_state=random_state)

    cv_results = cross_validate(
        model, x, y, cv=skf, scoring=["accuracy"], return_train_score=False
    )
    cv_pred = cross_val_predict(model, x, y, cv=skf)

    return {
        "cv_accuracy_mean": float(np.mean(cv_results["test_accuracy"])),
        "cv_accuracy_std": float(np.std(cv_results["test_accuracy"])),
        "cv_fold_accuracies": [float(a) for a in cv_results["test_accuracy"]],
        "cv_predictions": cv_pred,
    }


# ---------------------------------------------------------------------------
# Model comparison
# ---------------------------------------------------------------------------


def compare_models(
    models: dict[str, Pipeline],
    x: pd.DataFrame,
    y: pd.Series,
    *,
    n_splits: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """Run CV for each model and return a comparison DataFrame."""
    rows: list[dict[str, Any]] = []
    for name, model in models.items():
        result = evaluate_cross_validation(
            model, x, y, n_splits=n_splits, random_state=random_state
        )
        rows.append(
            {
                "model": name,
                "cv_accuracy_mean": result["cv_accuracy_mean"],
                "cv_accuracy_std": result["cv_accuracy_std"],
                "n_folds": len(result["cv_fold_accuracies"]),
                "warning": result.get("warning", ""),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rule-based classifier evaluation helpers
# ---------------------------------------------------------------------------


def evaluate_rule_classifier(
    feature_csv: str | Path,
) -> dict[str, Any]:
    """Evaluate the rule-based classifier against ground-truth labels.

    Reads *feature_csv* (output of ``main_rule_based``, containing
    ``label`` and ``rule_prediction`` columns), computes accuracy and
    a per-class breakdown.
    """
    df = pd.read_csv(feature_csv)
    required = {"label", "rule_prediction"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"CSV missing required columns: {missing}")

    labeled = df[df["label"].notna() & (df["label"].astype(str).str.strip() != "")].copy()
    if labeled.empty:
        return {"accuracy": float("nan"), "per_class": {}, "confusion": np.array([])}

    y_true = labeled["label"].astype(str)
    y_pred = labeled["rule_prediction"].astype(str)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "per_class": classification_report(y_true, y_pred, zero_division=0, output_dict=True),
        "confusion": confusion_matrix(y_true, y_pred),
    }


# ---------------------------------------------------------------------------
# Feature importance (for linear / logistic models)
# ---------------------------------------------------------------------------


def feature_coefficients(model: Pipeline) -> dict[str, float]:
    """Extract per-class feature coefficients from a linear classifier.

    Only works for LogisticRegression or linear-kernel SVM.
    """
    clf = model.named_steps.get("classifier")
    if clf is None or not hasattr(clf, "coef_"):
        return {}
    coef = clf.coef_
    classes = getattr(clf, "classes_", [str(i) for i in range(coef.shape[0])])
    result: dict[str, float] = {}
    for i, cls_name in enumerate(classes):
        for j, feat_name in enumerate(FEATURE_COLUMNS):
            result[f"{cls_name}__{feat_name}"] = float(coef[i, j])
    return result


def plot_feature_importance(
    importance: dict[str, float],
    path: str | Path,
    title: str = "Feature Coefficients",
    top_n: int = 20,
) -> None:
    """Save a horizontal bar chart of feature importances."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    items = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
    if not items:
        return

    names, values = zip(*items)
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in values]

    fig, ax = plt.subplots(figsize=(8, max(4, len(items) * 0.35)))
    ax.barh(range(len(names)), values, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Coefficient value")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
