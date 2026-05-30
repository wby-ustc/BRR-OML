from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, classification_report


def save_classification_report(y_true, y_pred, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(classification_report(y_true, y_pred), encoding="utf-8")


def save_confusion_matrix(y_true, y_pred, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay.from_predictions(y_true, y_pred)
    display.figure_.tight_layout()
    display.figure_.savefig(path, dpi=160)
    plt.close(display.figure_)
