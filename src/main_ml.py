from __future__ import annotations

import argparse
from datetime import datetime
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
    classes_present = set(y.unique())
    # All three banana ripeness classes required for a production model.
    has_full_classes = classes_present >= {"unripe", "ripe", "overripe"}
    can_split = n_classes >= 2

    if not has_full_classes and not args.allow_single_class:
        print(
            "ERROR: 缺少完整三分类数据 (unripe / ripe / overripe)。\n"
            f"当前类别: {sorted(classes_present)}\n"
            "请确保 data/raw/unripe/, ripe/, overripe/ 中均放置了样本图片，\n"
            "然后重新运行 python -m src.main_rule_based 生成特征表。\n"
            "如果仅用于调试，请添加 --allow-single-class 参数。"
        )
        raise SystemExit(1)

    # Feature CSV metadata (reused in model meta)
    feature_csv_mtime = datetime.fromtimestamp(feature_csv.stat().st_mtime).isoformat()

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

    # ---- 3a. Single-class debug mode -----------------------------------
    if not can_split:
        print(
            "\n⚠ 单类别调试模式：模型仅拟合当前数据，"
            "保存为 debug_single_class.pkl。\n"
            "  这些模型不能用于正式预测——它们只会输出唯一的类别。\n"
            "  要训练正式模型，请确保三类样本均已放置。"
        )
        for name, model in models.items():
            try:
                model.fit(x, y)
                # Save as debug file — NEVER overwrite the production model.
                debug_path = model_dir / f"{name}_debug_single_class.pkl"
                save_model(model, debug_path)
                print(f"  {name}: fitted on {len(x)} samples → {debug_path}")
            except ValueError as exc:
                print(f"  {name}: skipped — {exc}")
        print("\nDone (debug mode).")
        return

    # ---- 3b. Train/test split evaluation -------------------------------
    from sklearn.metrics import accuracy_score

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )
    print(f"\nTrain/test split: {len(x_train)} train, {len(x_test)} test")

    test_accuracies: dict[str, float] = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        acc = float(accuracy_score(y_test, pred))
        test_accuracies[name] = acc

        report_path = result_dir / f"{name}_classification_report.txt"
        report = save_classification_report(y_test, pred, report_path)
        print(f"\n--- {name} (test accuracy: {acc:.4f}) ---")
        print(report)

        cm_path = result_dir / f"{name}_confusion_matrix.png"
        save_confusion_matrix(y_test, pred, cm_path, title=f"{name.upper()} Confusion Matrix")
        print(f"Saved: {report_path}")

    # ---- 3c. Cross-validation ------------------------------------------
    cv_accuracies: dict[str, float] = {}
    if not args.no_cv:
        if y.value_counts().min() >= args.cv_splits:
            print(f"\n=== {args.cv_splits}-fold Cross-Validation ===")
            cv_comparison = compare_models(
                models, x, y, n_splits=args.cv_splits, random_state=args.random_state
            )
            # Extract mean CV accuracy per model
            for _, row in cv_comparison.iterrows():
                cv_accuracies[str(row.get("model", ""))] = float(
                    row.get("cv_accuracy_mean", 0.0)
                )
            print(cv_comparison.to_string(index=False))
            cv_comparison.to_csv(
                comparison_dir / "cv_comparison.csv", index=False, encoding="utf-8-sig"
            )
        else:
            print(
                f"\nSkipping CV: smallest class has {y.value_counts().min()} samples, "
                f"need ≥{args.cv_splits} for {args.cv_splits}-fold CV."
            )

    # ---- 3d. Final full-data models + metadata --------------------------
    # Train on ALL labeled data so the saved model benefits from every sample.
    # Only save if all three ripeness classes are present.
    print(f"\n=== Final model (trained on all {len(x)} samples) ===")

    from .ml_classifier import REQUIRED_CLASSES, save_model_meta

    class_counts = y.value_counts().to_dict()
    train_time = datetime.now().isoformat()

    for name, make_fn in [
        ("knn", make_knn),
        ("svm", make_svm),
        ("logistic", make_logistic),
    ]:
        model = make_fn(k=5) if name == "knn" else make_fn()
        model.fit(x, y)

        model_classes = set(str(c) for c in model.classes_)

        if model_classes != REQUIRED_CLASSES:
            print(
                f"  ⚠ {name}: 跳过保存 — 模型类别 {sorted(model_classes)} "
                f"≠ 需要 {sorted(REQUIRED_CLASSES)}。"
            )
            continue

        model_path = model_dir / f"{name}_model.pkl"
        save_model(model, model_path)

        meta: dict[str, Any] = {
            "model_name": name,
            "classes": sorted(model_classes),
            "class_counts": class_counts,
            "feature_csv": str(feature_csv),
            "feature_csv_mtime": feature_csv_mtime,
            "train_time": train_time,
            "n_samples": len(x),
            "test_accuracy": test_accuracies.get(name),
            "cv_accuracy": cv_accuracies.get(name),
        }
        save_model_meta(model_path, meta)
        print(
            f"  {name}_model.pkl: classes={sorted(model_classes)}, "
            f"n_samples={len(x)}, test_acc={test_accuracies.get(name, 'N/A'):.4f}"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
