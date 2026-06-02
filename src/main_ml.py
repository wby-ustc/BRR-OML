from __future__ import annotations

import argparse
from pathlib import Path

from .utils import ensure_dir, load_config, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train KNN/SVM from extracted feature CSV.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML.")
    parser.add_argument("--features", default=None, help="Path to combined_features.csv.")
    parser.add_argument("--test-size", type=float, default=0.3, help="Hold-out fraction.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--cv-splits", type=int, default=5, help="Number of cross-validation folds."
    )
    parser.add_argument(
        "--no-cv", action="store_true", help="Skip cross-validation; only train/test split."
    )
    parser.add_argument(
        "--no-baseline", action="store_true", help="Skip rule-classifier baseline comparison."
    )
    parser.add_argument(
        "--allow-single-class",
        action="store_true",
        help="Allow training when only one class is present (for debugging).",
    )
    return parser.parse_args()


def _check_minimum_data(x, y, test_size: float) -> None:
    """Warn or exit when data is insufficient for reliable training."""
    counts = y.value_counts().to_dict()
    print(f"Class distribution: {counts}")

    min_count = min(counts.values())
    test_samples_needed = max(1, int(min_count * test_size))
    if min_count < 3:
        print(
            f"WARNING: smallest class has only {min_count} sample(s). "
            "Train/test split and CV may be unreliable."
        )


def main() -> None:
    args = parse_args()

    try:
        from sklearn.model_selection import train_test_split

        from .evaluation import (
            compare_models,
            evaluate_cross_validation,
            evaluate_rule_classifier,
            save_classification_report,
            save_confusion_matrix,
        )
        from .ml_classifier import (
            load_feature_data,
            make_knn,
            make_logistic,
            make_svm,
            save_model,
        )
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Machine-learning dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    config = load_config(args.config)
    paths = config.get("paths", {})
    feature_csv = resolve_path(
        args.features or paths.get("feature_csv", "data/features/combined_features.csv")
    )
    model_dir = ensure_dir(resolve_path(paths.get("model_dir", "models")))
    result_dir = ensure_dir(resolve_path("results/machine_learning"))
    comparison_dir = ensure_dir(resolve_path("results/comparison"))

    # ------------------------------------------------------------------
    # 1. Load data ------------------------------------------------------
    # ------------------------------------------------------------------
    x, y = load_feature_data(feature_csv, allow_single_class=args.allow_single_class)
    print(f"Loaded {len(x)} labeled samples, {len(x.columns)} features.")
    _check_minimum_data(x, y, args.test_size)

    n_classes = y.nunique()
    can_split = n_classes >= 2

    # ------------------------------------------------------------------
    # 2. Rule-based baseline --------------------------------------------
    # ------------------------------------------------------------------
    if not args.no_baseline:
        summary_csv = resolve_path(
            paths.get("summary_csv", "results/rule_based/summary.csv")
        )
        rule_result = evaluate_rule_classifier(summary_csv)
        rule_acc = rule_result["accuracy"]
        print(f"\nRule-based baseline accuracy: {rule_acc:.4f}")
        # Write a short baseline summary.
        (comparison_dir / "baseline_rule.txt").write_text(
            f"rule_based_accuracy: {rule_acc:.4f}\n"
            f"n_samples: {len(x)}\n"
            f"classes: {sorted(y.unique())}\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # 3. Train models ---------------------------------------------------
    # ------------------------------------------------------------------
    models = {
        "knn": make_knn(k=5),
        "svm": make_svm(),
        "logistic": make_logistic(),
    }

    # 3a. Train/test split evaluation (only when ≥2 classes)
    if can_split:
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=args.test_size, random_state=args.random_state, stratify=y
        )
        print(f"\nTrain/test split: {len(x_train)} train, {len(x_test)} test")

        for name, model in models.items():
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            save_model(model, model_dir / f"{name}_model.pkl")

            report_path = result_dir / f"{name}_classification_report.txt"
            report = save_classification_report(y_test, pred, report_path)
            print(f"\n--- {name} ---")
            print(report)

            cm_path = result_dir / f"{name}_confusion_matrix.png"
            save_confusion_matrix(y_test, pred, cm_path, title=f"{name.upper()} Confusion Matrix")
            print(f"Saved: {report_path}")
    else:
        print(
            "\nSkipping train/test split — only 1 class present. "
            "Training on all data and saving models (usable for inference only)."
        )
        for name, model in models.items():
            try:
                model.fit(x, y)
                save_model(model, model_dir / f"{name}_model.pkl")
                print(f"  {name}: fitted on all {len(x)} samples, saved to {model_dir}")
            except ValueError as exc:
                print(f"  {name}: skipped — {exc}")

    # 3b. Cross-validation (when feasible)
    if not args.no_cv:
        if can_split and y.value_counts().min() >= args.cv_splits:
            print(f"\n=== {args.cv_splits}-fold Cross-Validation ===")
            cv_comparison = compare_models(
                models, x, y, n_splits=args.cv_splits, random_state=args.random_state
            )
            print(cv_comparison.to_string(index=False))
            cv_comparison.to_csv(
                comparison_dir / "cv_comparison.csv", index=False, encoding="utf-8-sig"
            )
        elif can_split:
            print(
                f"\nSkipping CV: smallest class has {y.value_counts().min()} samples, "
                f"need ≥{args.cv_splits} for {args.cv_splits}-fold CV."
            )
        else:
            print("\nSkipping CV: only 1 class present.")

    print("\nDone.")


if __name__ == "__main__":
    main()
