from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .dataset_builder import FEATURE_COLUMNS


def load_feature_data(csv_path: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(csv_path)
    labeled = df[df["label"].notna() & (df["label"].astype(str) != "")]
    if labeled.empty:
        raise ValueError("No labeled rows found. Put images under data/raw/unripe, ripe, overripe.")
    return labeled[FEATURE_COLUMNS], labeled["label"]


def make_knn(k: int = 5) -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("classifier", KNeighborsClassifier(n_neighbors=k))])


def make_svm() -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("classifier", SVC(kernel="rbf", C=10.0, gamma="scale"))])


def save_model(model: Pipeline, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
