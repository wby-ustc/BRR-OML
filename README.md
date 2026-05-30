# Banana Ripeness HGSK

Rule-based banana ripeness recognition using HSV color ratios and GLCM texture
features. The basic pipeline reads images, segments the banana region, extracts
features, classifies each image as `unripe`, `ripe`, or `overripe`, and writes
visual outputs plus a CSV summary.

## Project Layout

```text
data/raw/{unripe,ripe,overripe}/    Input images, grouped by optional labels
data/processed/masks/               Binary banana masks
data/processed/visualized/          Annotated result images
data/features/combined_features.csv Feature table for later ML experiments
results/rule_based/summary.csv      Rule-based prediction summary
src/main_rule_based.py              Basic version entry point
```

## Install

```bash
pip install -r requirements.txt
```

## Run Basic Version

Process all images under `data/raw`:

```bash
python -m src.main_rule_based --input data/raw --config config.yaml
```

Process one image:

```bash
python -m src.main_rule_based --input path/to/banana.jpg --config config.yaml
```

The default rule thresholds live in `config.yaml`. They are intentionally easy
to tune after checking the generated masks and summary CSV.
