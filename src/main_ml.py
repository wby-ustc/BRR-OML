from __future__ import annotations

import argparse
from pathlib import Path

from .utils import load_config, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train KNN/SVM from extracted feature CSV.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--features", default=None)
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from sklearn.model_selection import train_test_split

        from .evaluation import save_classification_report, save_confusion_matrix
        from .ml_classifier import load_feature_data, make_knn, make_svm, save_model
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Machine-learning dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    config = load_config(args.config)
    paths = config.get("paths", {})
    feature_csv = resolve_path(args.features or paths.get("feature_csv", "data/features/combined_features.csv"))
    model_dir = resolve_path(paths.get("model_dir", "models"))
    result_dir = resolve_path("results/machine_learning")

    x, y = load_feature_data(feature_csv)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )

    for name, model in {"knn": make_knn(), "svm": make_svm()}.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        save_model(model, model_dir / f"{name}_model.pkl")
        save_classification_report(y_test, pred, result_dir / f"{name}_classification_report.txt")
        save_confusion_matrix(y_test, pred, result_dir / f"{name}_confusion_matrix.png")
        print(f"{name}: saved model and evaluation files")


if __name__ == "__main__":
    main()
