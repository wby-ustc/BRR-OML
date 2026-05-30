# Banana Ripeness Recognition Report

## 1. Objective

Recognize banana ripeness with HSV color ratios, GLCM texture features, and a
rule-based classifier.

## 2. Dataset

Place images under:

- `data/raw/unripe`
- `data/raw/ripe`
- `data/raw/overripe`

## 3. Method

The basic version uses preprocessing, HSV segmentation, morphology cleanup,
largest connected component extraction, HSV feature extraction, GLCM feature
extraction, and threshold-based classification.

## 4. Results

Generated files:

- `results/rule_based/summary.csv`
- `data/features/combined_features.csv`
- `results/rule_based/images`

## 5. Analysis

Record segmentation failures, threshold changes, and confusing samples here.
