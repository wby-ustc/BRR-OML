from __future__ import annotations

import argparse

import pandas as pd

from .dataset_builder import extract_features_for_image
from .utils import ensure_dir, list_image_files, load_config, resolve_path, safe_stem, write_image
from .visualization import draw_prediction, make_side_by_side


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rule-based banana ripeness recognition.")
    parser.add_argument("--input", default="data/raw", help="Input image file or directory.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML.")
    parser.add_argument("--summary", default=None, help="Optional output CSV path.")
    parser.add_argument("--no-save-images", action="store_true", help="Only write CSV outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = config.get("paths", {})
    summary_path = resolve_path(args.summary or paths.get("summary_csv", "results/rule_based/summary.csv"))
    feature_csv = resolve_path(paths.get("feature_csv", "data/features/combined_features.csv"))
    mask_dir = ensure_dir(resolve_path(paths.get("mask_dir", "data/processed/masks")))
    visualized_dir = ensure_dir(resolve_path(paths.get("visualized_dir", "data/processed/visualized")))
    rule_image_dir = ensure_dir(resolve_path(paths.get("rule_image_dir", "results/rule_based/images")))

    image_files = list_image_files(args.input)
    if not image_files:
        raise SystemExit(f"No image files found under: {args.input}")

    rows = []
    for image_path in image_files:
        row, processed, mask = extract_features_for_image(image_path, config)
        rows.append(row)

        if not args.no_save_images:
            stem = safe_stem(image_path)
            prediction = row["rule_prediction"]
            annotated = draw_prediction(processed, mask, prediction)
            comparison = make_side_by_side(processed, mask, annotated)
            write_image(mask_dir / f"{stem}_mask.png", mask)
            write_image(visualized_dir / f"{stem}_visualized.jpg", annotated)
            write_image(rule_image_dir / f"{stem}_comparison.jpg", comparison)

        print(f"{image_path} -> {prediction}")

    df = pd.DataFrame(rows)
    ensure_dir(summary_path.parent)
    ensure_dir(feature_csv.parent)
    df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    df.to_csv(feature_csv, index=False, encoding="utf-8-sig")
    print(f"Saved summary: {summary_path}")
    print(f"Saved features: {feature_csv}")


if __name__ == "__main__":
    main()
