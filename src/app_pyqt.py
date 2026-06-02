"""PyQt5 桌面应用：基于 OpenCV 与机器学习的香蕉成熟度识别应用系统。

启动方式::

    python -m src.app_pyqt          # 模块运行（推荐）
    python src/app_pyqt.py          # 直接脚本运行（也支持）

功能:
    - 单张图片识别：原图 / 分割 mask / 识别结果图 + 特征值表格
    - 批量检测：遍历文件夹 + 结果表格 + CSV 导出
    - 分类方法选择：规则分类 / KNN / SVM / Logistic
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 兼容直接脚本运行：当用户点击 VSCode "Run Python File" 或执行
# ``python src/app_pyqt.py`` 时，Python 不会自动将文件识别为包成员，
# 导致相对导入 ``from .xxx import`` 失败。此处通过设置 __package__ 和
# sys.path 使两种运行方式均正常工作。
# ---------------------------------------------------------------------------
if __name__ == "__main__" and __package__ is None:
    _project_root = Path(__file__).resolve().parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    __package__ = "src"

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# 项目内部模块
# ---------------------------------------------------------------------------
from .dataset_builder import FEATURE_COLUMNS, extract_features_for_image
from .ml_classifier import load_model, predict_single
from .rule_classifier import classify_by_rules
from .utils import (
    IMAGE_EXTENSIONS,
    ensure_dir,
    list_image_files,
    load_config,
    project_root,
    read_image,
    resolve_path,
)
from .visualization import LABEL_COLORS, draw_prediction, overlay_mask

# ---------------------------------------------------------------------------
# PyQt5 导入（含友好报错）
# ---------------------------------------------------------------------------
try:
    from PyQt5.QtCore import QThread, Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QImage, QPixmap
    from PyQt5.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSplitter,
        QStatusBar,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    print("错误：未安装 PyQt5。请执行: pip install PyQt5")
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
WINDOW_TITLE = "基于 OpenCV 与机器学习的香蕉成熟度识别应用系统"
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
IMAGE_DISPLAY_SIZE = 380

CLASS_METHODS = ["规则分类", "KNN", "SVM", "Logistic"]

METHOD_TO_MODEL = {
    "KNN": "knn_model.pkl",
    "SVM": "svm_model.pkl",
    "Logistic": "logistic_model.pkl",
}

ADVICE: dict[str, str] = {
    "unripe": "香蕉尚未成熟，建议放置 3–5 天后食用。",
    "ripe": "香蕉已成熟，适合立即食用。",
    "overripe": "香蕉过熟，建议尽快食用或用于烘焙。",
    "unknown": "无法确定成熟度，请检查图片质量或分割效果。",
}

DISPLAY_FEATURES = [
    "green_ratio",
    "yellow_ratio",
    "dark_ratio",
    "H_mean",
    "S_mean",
    "V_mean",
    "glcm_contrast",
    "glcm_energy",
    "glcm_homogeneity",
]

FEATURE_LABELS: dict[str, str] = {
    "green_ratio": "绿色比例 (green_ratio)",
    "yellow_ratio": "黄色比例 (yellow_ratio)",
    "dark_ratio": "暗色比例 (dark_ratio)",
    "H_mean": "H 均值 (H_mean)",
    "S_mean": "S 均值 (S_mean)",
    "V_mean": "V 均值 (V_mean)",
    "glcm_contrast": "GLCM 对比度 (contrast)",
    "glcm_energy": "GLCM 能量 (energy)",
    "glcm_homogeneity": "GLCM 同质性 (homogeneity)",
}


# ---------------------------------------------------------------------------
# 工具函数：OpenCV ↔ Qt 图像转换
# ---------------------------------------------------------------------------


def cv_to_qpixmap(image_bgr: np.ndarray, target_size: int | None = None) -> QPixmap:
    """将 OpenCV BGR 图像转换为 QPixmap，可选缩放至 target_size 内。"""
    if image_bgr is None or image_bgr.size == 0:
        return QPixmap()
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qimg)
    if target_size:
        pixmap = pixmap.scaled(
            target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
    return pixmap


def mask_to_qpixmap(mask: np.ndarray, target_size: int | None = None) -> QPixmap:
    """将二值 mask (0/255) 转换为彩色 QPixmap 用于显示。"""
    if mask is None or mask.size == 0 or np.count_nonzero(mask) == 0:
        # 返回一个带提示文字的空白图
        blank = np.zeros((200, 200, 3), dtype=np.uint8)
        blank[:] = (240, 240, 240)
        cv2.putText(
            blank,
            "无有效分割区域",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (100, 100, 100),
            2,
            cv2.LINE_AA,
        )
        return cv_to_qpixmap(blank, target_size)
    colored = cv2.applyColorMap(mask, cv2.COLORMAP_VIRIDIS)
    return cv_to_qpixmap(colored, target_size)


def blank_placeholder(text: str = "暂无图片") -> QPixmap:
    """生成占位空白图。"""
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    blank[:] = (245, 245, 245)
    cv2.putText(
        blank,
        text,
        (35, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (150, 150, 150),
        1,
        cv2.LINE_AA,
    )
    return cv_to_qpixmap(blank)


# ---------------------------------------------------------------------------
# 批量处理工作线程
# ---------------------------------------------------------------------------


class BatchWorker(QThread):
    """在后台线程中批量处理图片，通过信号将结果发送到主线程。"""

    progress = pyqtSignal(int, int)  # current, total
    result_ready = pyqtSignal(dict)  # 单条结果
    image_error = pyqtSignal(str, str)  # (image_path, error_message)
    finished = pyqtSignal()

    def __init__(
        self,
        image_paths: list[Path],
        config: dict[str, Any],
        method: str,
        model_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._image_paths = image_paths
        self._config = config
        self._method = method
        self._model_dir = model_dir

    def run(self) -> None:
        total = len(self._image_paths)

        # 如果选择了 ML 方法，提前加载模型（避免每张图重复加载）
        model = None
        if self._method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[self._method]
            if model_path.exists():
                model = load_model(model_path)

        for idx, image_path in enumerate(self._image_paths):
            try:
                row, processed, mask = extract_features_for_image(image_path, self._config)
            except Exception as exc:
                self.image_error.emit(str(image_path), str(exc))
                self.progress.emit(idx + 1, total)
                continue

            features = {c: row.get(c, 0.0) for c in FEATURE_COLUMNS}

            # 分类
            if self._method == "规则分类":
                prediction = row.get("rule_prediction", "unknown")
                proba = {}
            elif model is not None:
                try:
                    prediction, proba = predict_single(model, features)
                except Exception:
                    prediction = row.get("rule_prediction", "unknown")
                    proba = {}
            else:
                # 模型文件不存在，回退到规则分类
                prediction = classify_by_rules(features, self._config.get("rules", {}))
                proba = {}

            result = {
                "image_path": str(image_path),
                "prediction": prediction,
                "green_ratio": features.get("green_ratio", 0.0),
                "yellow_ratio": features.get("yellow_ratio", 0.0),
                "dark_ratio": features.get("dark_ratio", 0.0),
                "H_mean": features.get("H_mean", 0.0),
                "S_mean": features.get("S_mean", 0.0),
                "V_mean": features.get("V_mean", 0.0),
                "glcm_contrast": features.get("glcm_contrast", 0.0),
                "glcm_energy": features.get("glcm_energy", 0.0),
                "glcm_homogeneity": features.get("glcm_homogeneity", 0.0),
            }
            self.result_ready.emit(result)
            self.progress.emit(idx + 1, total)

        self.finished.emit()


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # ---------- 状态 ----------
        self._config: dict[str, Any] = {}
        self._current_image_path: str | None = None
        self._current_folder_path: str | None = None
        self._batch_results: list[dict[str, Any]] = []
        self._batch_worker: BatchWorker | None = None

        # 当前处理结果缓存（用于显示）
        self._current_original: np.ndarray | None = None
        self._current_mask: np.ndarray | None = None
        self._current_result_img: np.ndarray | None = None
        self._current_prediction: str = ""
        self._current_features: dict[str, float] = {}

        self._load_config()
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        try:
            self._config = load_config("config.yaml")
        except Exception as exc:
            QMessageBox.warning(self, "配置加载失败", f"无法读取 config.yaml：{exc}")

    @property
    def _model_dir(self) -> Path:
        paths = self._config.get("paths", {})
        return resolve_path(paths.get("model_dir", "models"))

    # ------------------------------------------------------------------
    # 界面构建
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # ---- 工具栏 ----
        root_layout.addLayout(self._build_toolbar())

        # ---- 中部：图像显示 + 信息区（垂直分割） ----
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._build_image_panel())
        splitter.addWidget(self._build_info_panel())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        root_layout.addWidget(splitter, stretch=1)

        # ---- 状态栏 ----
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪 — 请打开图片或选择文件夹后点击「开始识别」")

    def _build_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self._btn_open_image = QPushButton("📂 打开图片")
        self._btn_open_image.setMinimumHeight(34)
        layout.addWidget(self._btn_open_image)

        self._btn_open_folder = QPushButton("📁 选择文件夹")
        self._btn_open_folder.setMinimumHeight(34)
        layout.addWidget(self._btn_open_folder)

        layout.addSpacing(16)

        method_label = QLabel("分类方法：")
        layout.addWidget(method_label)

        self._combo_method = QComboBox()
        self._combo_method.addItems(CLASS_METHODS)
        self._combo_method.setMinimumWidth(100)
        layout.addWidget(self._combo_method)

        layout.addSpacing(8)

        self._btn_start = QPushButton("▶ 开始识别")
        self._btn_start.setMinimumHeight(34)
        self._btn_start.setStyleSheet(
            "QPushButton { background-color: #2ca02c; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #3cb03c; }"
        )
        layout.addWidget(self._btn_start)

        layout.addSpacing(16)

        self._btn_export = QPushButton("💾 导出 CSV")
        self._btn_export.setMinimumHeight(34)
        self._btn_export.setEnabled(False)
        layout.addWidget(self._btn_export)

        layout.addStretch()
        return layout

    def _build_image_panel(self) -> QWidget:
        """三个图像显示面板：原图 | Mask | 结果图。"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 原图
        g1 = QGroupBox("原图")
        g1_layout = QVBoxLayout(g1)
        self._lbl_original = QLabel()
        self._lbl_original.setAlignment(Qt.AlignCenter)
        self._lbl_original.setMinimumSize(IMAGE_DISPLAY_SIZE, IMAGE_DISPLAY_SIZE)
        self._lbl_original.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_original.setPixmap(blank_placeholder("暂无图片"))
        g1_layout.addWidget(self._lbl_original)
        layout.addWidget(g1)

        # Mask
        g2 = QGroupBox("分割 Mask")
        g2_layout = QVBoxLayout(g2)
        self._lbl_mask = QLabel()
        self._lbl_mask.setAlignment(Qt.AlignCenter)
        self._lbl_mask.setMinimumSize(IMAGE_DISPLAY_SIZE, IMAGE_DISPLAY_SIZE)
        self._lbl_mask.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_mask.setPixmap(blank_placeholder("暂无数据"))
        g2_layout.addWidget(self._lbl_mask)
        layout.addWidget(g2)

        # 结果图
        g3 = QGroupBox("识别结果")
        g3_layout = QVBoxLayout(g3)
        self._lbl_result = QLabel()
        self._lbl_result.setAlignment(Qt.AlignCenter)
        self._lbl_result.setMinimumSize(IMAGE_DISPLAY_SIZE, IMAGE_DISPLAY_SIZE)
        self._lbl_result.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_result.setPixmap(blank_placeholder("暂无结果"))
        g3_layout.addWidget(self._lbl_result)
        layout.addWidget(g3)

        return container

    def _build_info_panel(self) -> QWidget:
        """底部信息区：预测结果 + 食用建议 + 特征表格 + 批量结果表格。"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # 预测 + 建议行
        info_row = QHBoxLayout()
        info_row.setSpacing(24)

        pred_label = QLabel("预测类别：")
        pred_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        info_row.addWidget(pred_label)

        self._lbl_prediction = QLabel("—")
        self._lbl_prediction.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self._lbl_prediction.setStyleSheet("QLabel { color: #1f77b4; }")
        info_row.addWidget(self._lbl_prediction)

        info_row.addSpacing(24)

        advice_label = QLabel("食用建议：")
        advice_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        info_row.addWidget(advice_label)

        self._lbl_advice = QLabel("—")
        self._lbl_advice.setFont(QFont("Microsoft YaHei", 10))
        self._lbl_advice.setWordWrap(True)
        info_row.addWidget(self._lbl_advice)

        info_row.addStretch()
        layout.addLayout(info_row)

        # 特征表格
        self._table_features = QTableWidget()
        self._table_features.setColumnCount(2)
        self._table_features.setHorizontalHeaderLabels(["特征名称", "特征值"])
        self._table_features.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table_features.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table_features.setMaximumHeight(220)
        self._table_features.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_features.setAlternatingRowColors(True)
        self._populate_feature_table({})
        layout.addWidget(self._table_features)

        # 批量结果表格
        self._table_batch = QTableWidget()
        self._table_batch.setColumnCount(10)
        self._table_batch.setHorizontalHeaderLabels([
            "图片路径", "预测类别",
            "green_ratio", "yellow_ratio", "dark_ratio",
            "H_mean", "S_mean", "V_mean",
            "glcm_contrast", "glcm_homogeneity",
        ])
        self._table_batch.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 10):
            self._table_batch.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self._table_batch.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_batch.setAlternatingRowColors(True)
        self._table_batch.setVisible(False)
        layout.addWidget(self._table_batch)

        return container

    # ------------------------------------------------------------------
    # 信号连接
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._btn_open_image.clicked.connect(self._on_open_image)
        self._btn_open_folder.clicked.connect(self._on_open_folder)
        self._btn_start.clicked.connect(self._on_start_recognition)
        self._btn_export.clicked.connect(self._on_export_csv)

    # ------------------------------------------------------------------
    # 槽函数
    # ------------------------------------------------------------------

    def _on_open_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择香蕉图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp);;所有文件 (*)",
        )
        if file_path:
            self._current_image_path = file_path
            self._current_folder_path = None
            self._batch_results.clear()
            self._table_batch.setVisible(False)
            self._table_batch.setRowCount(0)
            self._btn_export.setEnabled(False)
            self._status_bar.showMessage(f"已选择图片：{file_path}")
            self._show_selected_image_preview(file_path)
            self._update_ui_state()

    def _show_selected_image_preview(self, image_path: str) -> None:
        """在打开图片后立即显示原图预览（尚未识别）。"""
        try:
            original = read_image(image_path)
            self._lbl_original.setPixmap(cv_to_qpixmap(original, IMAGE_DISPLAY_SIZE))
            self._lbl_mask.setPixmap(blank_placeholder("点击「开始识别」"))
            self._lbl_result.setPixmap(blank_placeholder("点击「开始识别」"))
        except Exception as exc:
            QMessageBox.warning(self, "图片读取失败", f"无法读取图片：{exc}")

    def _on_open_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder_path:
            self._current_folder_path = folder_path
            self._current_image_path = None
            self._batch_results.clear()
            self._table_batch.setVisible(False)
            self._table_batch.setRowCount(0)
            self._btn_export.setEnabled(False)

            # 统计图片数量
            image_files = list_image_files(folder_path)
            self._status_bar.showMessage(
                f"已选择文件夹：{folder_path}（检测到 {len(image_files)} 张图片）"
            )

            # 清除单图显示
            self._lbl_original.setPixmap(blank_placeholder("批量模式"))
            self._lbl_mask.setPixmap(blank_placeholder("批量模式"))
            self._lbl_result.setPixmap(blank_placeholder("批量模式"))
            self._lbl_prediction.setText("—")
            self._lbl_advice.setText("—")
            self._populate_feature_table({})

            self._update_ui_state()

    def _on_start_recognition(self) -> None:
        method = self._combo_method.currentText()

        # 检查 ML 模型文件是否存在
        if method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if not model_path.exists():
                reply = QMessageBox.question(
                    self,
                    "模型文件不存在",
                    f"模型文件 {model_path} 不存在。\n\n"
                    "您可以：\n"
                    "  • 点击「Yes」回退到规则分类进行识别\n"
                    "  • 点击「No」取消操作，先训练模型",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    self._combo_method.setCurrentText("规则分类")
                    self._status_bar.showMessage("已切换为规则分类模式（模型文件不存在）")
                    self._do_single_recognition()
                    return
                else:
                    self._status_bar.showMessage(
                        f"请先运行 python -m src.main_ml 训练 {method} 模型，再使用该分类方法。"
                    )
                    return

        if self._current_image_path:
            self._do_single_recognition()
        elif self._current_folder_path:
            self._do_batch_recognition()
        else:
            QMessageBox.information(self, "提示", "请先打开一张图片或选择一个文件夹。")

    def _do_single_recognition(self) -> None:
        """处理单张图片识别。"""
        if not self._current_image_path:
            return

        method = self._combo_method.currentText()

        try:
            # 读取原图用于展示
            original = read_image(self._current_image_path)

            # 使用统一流水线提取特征 + 规则分类结果
            row, processed, mask = extract_features_for_image(
                self._current_image_path, self._config
            )
        except Exception as exc:
            QMessageBox.critical(self, "处理失败", f"图片处理过程中发生错误：{exc}")
            self._status_bar.showMessage("处理失败")
            return

        features = {c: row.get(c, 0.0) for c in FEATURE_COLUMNS}

        # 根据分类方法获取预测
        if method == "规则分类":
            prediction = row.get("rule_prediction", "unknown")
            proba_text = ""
        else:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if model_path.exists():
                try:
                    model = load_model(model_path)
                    prediction, proba = predict_single(model, features)
                    # 构建置信度文本
                    if proba:
                        parts = [f"{cls}: {p:.2%}" for cls, p in sorted(proba.items(), key=lambda x: -x[1])]
                        proba_text = " | ".join(parts)
                    else:
                        proba_text = ""
                except Exception as exc:
                    QMessageBox.warning(self, "模型预测失败", f"ML 预测出错，回退到规则分类：{exc}")
                    prediction = classify_by_rules(features, self._config.get("rules", {}))
                    proba_text = ""
            else:
                prediction = row.get("rule_prediction", "unknown")
                proba_text = ""

        # 生成结果图
        result_img = draw_prediction(processed, mask, prediction, proba_text)

        # 缓存
        self._current_original = original
        self._current_mask = mask
        self._current_result_img = result_img
        self._current_prediction = prediction
        self._current_features = {k: features.get(k, 0.0) for k in DISPLAY_FEATURES}

        # 更新 UI
        self._display_results()
        self._status_bar.showMessage(f"识别完成 — 预测类别：{prediction}（方法：{method}）")

    def _do_batch_recognition(self) -> None:
        """启动批量识别线程。"""
        if not self._current_folder_path:
            return

        image_files = list_image_files(self._current_folder_path)
        if not image_files:
            QMessageBox.information(self, "提示", "所选文件夹中没有图片文件。")
            return

        method = self._combo_method.currentText()

        # 检查 ML 模型
        if method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if not model_path.exists():
                QMessageBox.warning(
                    self,
                    "模型文件不存在",
                    f"{method} 模型文件不存在，将回退到规则分类。\n"
                    f"请运行 python -m src.main_ml 训练模型。",
                )
                self._combo_method.setCurrentText("规则分类")
                method = "规则分类"

        self._batch_results.clear()
        self._table_batch.setRowCount(0)
        self._table_batch.setVisible(True)
        self._btn_export.setEnabled(False)

        self._btn_start.setEnabled(False)
        self._status_bar.showMessage(f"批量处理中... 0/{len(image_files)}")

        self._batch_worker = BatchWorker(
            image_files, self._config, method, self._model_dir
        )
        self._batch_worker.progress.connect(self._on_batch_progress)
        self._batch_worker.result_ready.connect(self._on_batch_result)
        self._batch_worker.image_error.connect(self._on_batch_error)
        self._batch_worker.finished.connect(self._on_batch_finished)
        self._batch_worker.start()

    def _on_batch_progress(self, current: int, total: int) -> None:
        self._status_bar.showMessage(f"批量处理中... {current}/{total}")

    def _on_batch_result(self, result: dict[str, Any]) -> None:
        self._batch_results.append(result)
        row_idx = self._table_batch.rowCount()
        self._table_batch.insertRow(row_idx)

        columns = [
            result["image_path"],
            result["prediction"],
            f"{result['green_ratio']:.4f}",
            f"{result['yellow_ratio']:.4f}",
            f"{result['dark_ratio']:.4f}",
            f"{result['H_mean']:.2f}",
            f"{result['S_mean']:.2f}",
            f"{result['V_mean']:.2f}",
            f"{result['glcm_contrast']:.4f}",
            f"{result['glcm_homogeneity']:.4f}",
        ]
        for col, value in enumerate(columns):
            item = QTableWidgetItem(str(value))
            if col == 1:
                # 预测类别着色
                color = LABEL_COLORS.get(str(result["prediction"]), (220, 220, 220))
                item.setBackground(
                    QApplication.palette().window().color()  # 用默认背景，避免过度着色
                )
                # 用前景色区分
                b, g, r = int(color[0]), int(color[1]), int(color[2])
                item.setForeground(QApplication.palette().windowText().color())
            self._table_batch.setItem(row_idx, col, item)

    def _on_batch_error(self, image_path: str, error: str) -> None:
        self._status_bar.showMessage(f"处理出错 ({Path(image_path).name}): {error}")

    def _on_batch_finished(self) -> None:
        self._btn_start.setEnabled(True)
        n = len(self._batch_results)
        self._btn_export.setEnabled(n > 0)
        self._status_bar.showMessage(f"批量处理完成 — 共处理 {n} 张图片")
        if n == 0:
            QMessageBox.information(self, "提示", "未成功处理任何图片。")

    def _on_export_csv(self) -> None:
        """导出批量结果到 CSV 文件。"""
        if not self._batch_results:
            QMessageBox.information(self, "提示", "没有可导出的结果。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 CSV",
            "batch_results.csv",
            "CSV 文件 (*.csv);;所有文件 (*)",
        )
        if not file_path:
            return

        try:
            fieldnames = [
                "image_path", "prediction",
                "green_ratio", "yellow_ratio", "dark_ratio",
                "H_mean", "S_mean", "V_mean",
                "glcm_contrast", "glcm_energy", "glcm_homogeneity",
            ]
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(self._batch_results)
            self._status_bar.showMessage(f"已导出 CSV：{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"CSV 导出出错：{exc}")

    # ------------------------------------------------------------------
    # UI 更新
    # ------------------------------------------------------------------

    def _update_ui_state(self) -> None:
        """根据当前模式启用/禁用控件。"""
        has_image = self._current_image_path is not None
        has_folder = self._current_folder_path is not None
        has_target = has_image or has_folder
        self._btn_start.setEnabled(has_target)

    def _display_results(self) -> None:
        """将当前缓存的识别结果显示到界面。"""
        # 图像
        self._lbl_original.setPixmap(
            cv_to_qpixmap(self._current_original, IMAGE_DISPLAY_SIZE)
            if self._current_original is not None
            else blank_placeholder("暂无图片")
        )
        self._lbl_mask.setPixmap(
            mask_to_qpixmap(self._current_mask, IMAGE_DISPLAY_SIZE)
            if self._current_mask is not None
            else blank_placeholder("暂无数据")
        )
        self._lbl_result.setPixmap(
            cv_to_qpixmap(self._current_result_img, IMAGE_DISPLAY_SIZE)
            if self._current_result_img is not None
            else blank_placeholder("暂无结果")
        )

        # 预测 + 建议
        pred = self._current_prediction or "unknown"
        self._lbl_prediction.setText(pred)
        color = LABEL_COLORS.get(pred, LABEL_COLORS["unknown"])
        self._lbl_prediction.setStyleSheet(
            f"QLabel {{ color: rgb({color[2]},{color[1]},{color[0]}); font-weight: bold; }}"
        )
        self._lbl_advice.setText(ADVICE.get(pred, ADVICE["unknown"]))

        # 特征表格
        self._populate_feature_table(self._current_features)

    def _populate_feature_table(self, features: dict[str, float]) -> None:
        """填充特征值表格。"""
        self._table_features.setRowCount(len(DISPLAY_FEATURES))
        for i, key in enumerate(DISPLAY_FEATURES):
            label = FEATURE_LABELS.get(key, key)
            self._table_features.setItem(i, 0, QTableWidgetItem(label))
            value = features.get(key, None)
            if value is not None:
                # 根据特征类型选择合适的格式
                if "ratio" in key:
                    text = f"{value:.4f}"
                elif "glcm" in key:
                    text = f"{value:.4f}"
                else:
                    text = f"{value:.2f}"
                self._table_features.setItem(i, 1, QTableWidgetItem(text))
            else:
                self._table_features.setItem(i, 1, QTableWidgetItem("—"))


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> None:
    """启动 PyQt5 桌面应用。"""
    # Windows 下高 DPI 适配
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 设置默认字体，确保中文正常显示
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
