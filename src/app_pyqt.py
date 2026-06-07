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
import math
import sys
import time
from collections import deque
from datetime import datetime
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
from .inference import run_inference_on_frame
from .ml_classifier import (
    load_model,
    load_model_meta,
    predict_single,
    validate_model_classes,
)
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
    from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QImage, QPixmap
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
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
IMAGE_DISPLAY_SIZE = 280  # 图像面板显示尺寸（缩小以节省垂直空间）

CLASS_METHODS = ["规则分类", "KNN", "SVM", "Logistic"]  # 进阶版开放全部四种分类方法

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

# 摄像头实时稳定性参数（与 config.yaml stability 节保持默认一致）
STABILITY_CONFIRM_FRAMES = 3  # 连续检测到香蕉的帧数，确认后开始显示成熟度
STABILITY_LOST_FRAMES = 2     # 连续未检测到的帧数，确认后显示"未检测到香蕉"


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

        # 如果选择了 ML 方法，提前加载并验证模型
        model = None
        model_invalid = False
        model_missing = False
        if self._method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[self._method]
            if model_path.exists():
                model = load_model(model_path)
                valid, reason = validate_model_classes(model)
                if not valid:
                    model = None
                    model_invalid = True
            else:
                model_missing = True

        for idx, image_path in enumerate(self._image_paths):
            try:
                row, processed, mask = extract_features_for_image(image_path, self._config)
            except Exception as exc:
                self.image_error.emit(str(image_path), str(exc))
                self.progress.emit(idx + 1, total)
                continue

            features = {c: row.get(c, 0.0) for c in FEATURE_COLUMNS}

            # 分类 — track method_used and proba
            method_used = self._method
            proba: dict[str, float] = {}
            confidence: float = 0.0

            if self._method == "规则分类":
                prediction = row.get("rule_prediction", "unknown")
            elif model is not None:
                try:
                    prediction, proba = predict_single(model, features)
                    confidence = max(proba.values()) if proba else 0.0
                except Exception:
                    prediction = classify_by_rules(features, self._config.get("rules", {}))
                    method_used = f"规则分类（{self._method} 异常回退）"
            else:
                # 模型文件不存在或模型无效，回退到规则分类
                prediction = classify_by_rules(features, self._config.get("rules", {}))
                if model_missing:
                    method_used = f"规则分类（{self._method} 模型不存在）"
                elif model_invalid:
                    method_used = f"规则分类（{self._method} 类别不完整）"

            result = {
                "image_path": str(image_path),
                "prediction": prediction,
                "method_requested": self._method,
                "method_used": method_used,
                "confidence": confidence,
                "prob_overripe": proba.get("overripe", 0.0),
                "prob_ripe": proba.get("ripe", 0.0),
                "prob_unripe": proba.get("unripe", 0.0),
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

        # ---------- 摄像头状态 ----------
        self._camera_cap: cv2.VideoCapture | None = None
        self._camera_timer: QTimer | None = None
        self._camera_paused: bool = False
        self._camera_frame: np.ndarray | None = None
        self._last_inference_time: float = 0.0
        self._model_cache: dict[str, Any] = {}
        self._camera_fallback_msg: str = ""

        # 摄像头稳定性状态（多帧确认，避免闪烁）
        self._banana_votes: int = 0  # 0..confirm_frames，香蕉检测投票计数
        self._banana_confirmed: bool = False  # 当前是否已确认画面中有香蕉

        # 概率平滑历史（摄像头实时模式 ML 概率滑动窗口）
        self._proba_history: deque[dict[str, float]] = deque(maxlen=5)  # 运行时按 smooth_window 调整

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
        root_layout.addWidget(self._build_camera_toolbar())

        # ---- 中部：图像显示 + 信息区（垂直分割） ----
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._build_image_panel())
        splitter.addWidget(self._build_info_panel())
        splitter.setStretchFactor(0, 3)
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
        self._btn_export.setToolTip("批量检测完成后可导出 CSV 结果文件")
        layout.addWidget(self._btn_export)

        layout.addStretch()
        return layout

    def _build_camera_toolbar(self) -> QGroupBox:
        """摄像头控制工具栏。"""
        group = QGroupBox("📷 摄像头实时识别")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self._btn_camera_open = QPushButton("📷 打开摄像头")
        self._btn_camera_open.setMinimumHeight(32)
        layout.addWidget(self._btn_camera_open)

        self._btn_camera_close = QPushButton("❌ 关闭摄像头")
        self._btn_camera_close.setMinimumHeight(32)
        self._btn_camera_close.setEnabled(False)
        layout.addWidget(self._btn_camera_close)

        self._btn_camera_pause = QPushButton("⏸ 暂停")
        self._btn_camera_pause.setMinimumHeight(32)
        self._btn_camera_pause.setEnabled(False)
        layout.addWidget(self._btn_camera_pause)

        self._btn_camera_screenshot = QPushButton("📸 截图识别")
        self._btn_camera_screenshot.setMinimumHeight(32)
        self._btn_camera_screenshot.setEnabled(False)
        layout.addWidget(self._btn_camera_screenshot)

        layout.addSpacing(12)

        cam_id_label = QLabel("摄像头编号：")
        layout.addWidget(cam_id_label)

        self._spin_camera_id = QSpinBox()
        self._spin_camera_id.setRange(0, 9)
        self._spin_camera_id.setValue(0)
        self._spin_camera_id.setMinimumWidth(50)
        self._spin_camera_id.setToolTip("选择摄像头设备编号（默认 0 为前置摄像头）")
        layout.addWidget(self._spin_camera_id)

        layout.addSpacing(8)

        self._chk_mirror = QCheckBox("镜像翻转")
        self._chk_mirror.setChecked(False)
        self._chk_mirror.setToolTip("水平翻转画面（前置摄像头通常需要开启）")
        layout.addWidget(self._chk_mirror)

        layout.addStretch()
        return group

    def _build_image_panel(self) -> QWidget:
        """三个图像显示面板：原图 | Mask | 结果图。"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        from PyQt5.QtWidgets import QSizePolicy

        # 原图
        g1 = QGroupBox("原图")
        g1_layout = QVBoxLayout(g1)
        g1_layout.setContentsMargins(2, 2, 2, 2)
        self._lbl_original = QLabel()
        self._lbl_original.setAlignment(Qt.AlignCenter)
        self._lbl_original.setMinimumSize(200, 150)
        self._lbl_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_original.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_original.setPixmap(blank_placeholder("暂无图片"))
        g1_layout.addWidget(self._lbl_original)
        layout.addWidget(g1)

        # Mask
        g2 = QGroupBox("分割 Mask")
        g2_layout = QVBoxLayout(g2)
        g2_layout.setContentsMargins(2, 2, 2, 2)
        self._lbl_mask = QLabel()
        self._lbl_mask.setAlignment(Qt.AlignCenter)
        self._lbl_mask.setMinimumSize(200, 150)
        self._lbl_mask.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_mask.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_mask.setPixmap(blank_placeholder("暂无数据"))
        g2_layout.addWidget(self._lbl_mask)
        layout.addWidget(g2)

        # 结果图
        g3 = QGroupBox("识别结果")
        g3_layout = QVBoxLayout(g3)
        g3_layout.setContentsMargins(2, 2, 2, 2)
        self._lbl_result = QLabel()
        self._lbl_result.setAlignment(Qt.AlignCenter)
        self._lbl_result.setMinimumSize(200, 150)
        self._lbl_result.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_result.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ccc; }")
        self._lbl_result.setPixmap(blank_placeholder("暂无结果"))
        g3_layout.addWidget(self._lbl_result)
        layout.addWidget(g3)

        return container

    def _build_info_panel(self) -> QWidget:
        """底部信息区：预测结果 + 食用建议 + 特征表格 + 批量结果表格。"""
        container = QWidget()
        container.setMaximumHeight(260)  # 限制信息区高度，避免大面积空白
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(2)

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

        # 规则集 + 候选验证原因行
        self._lbl_ruleset = QLabel("")
        self._lbl_ruleset.setFont(QFont("Microsoft YaHei", 9))
        self._lbl_ruleset.setStyleSheet("QLabel { color: #666666; }")
        info_row.addWidget(self._lbl_ruleset)

        layout.addLayout(info_row)

        # 候选验证失败原因行（仅摄像头模式下有内容）
        self._lbl_candidate_reason = QLabel("")
        self._lbl_candidate_reason.setFont(QFont("Microsoft YaHei", 9))
        self._lbl_candidate_reason.setWordWrap(True)
        self._lbl_candidate_reason.setStyleSheet("QLabel { color: #cc6600; }")
        self._lbl_candidate_reason.setVisible(False)
        layout.addWidget(self._lbl_candidate_reason)

        # ML 模型概率 / 置信度 / 方法信息行
        self._lbl_proba = QLabel("")
        self._lbl_proba.setFont(QFont("Microsoft YaHei", 9))
        self._lbl_proba.setWordWrap(True)
        self._lbl_proba.setStyleSheet("QLabel { color: #444444; }")
        self._lbl_proba.setVisible(False)
        layout.addWidget(self._lbl_proba)

        # 特征表格（移除最大高度限制，允许表格充分利用下方空间）
        self._table_features = QTableWidget()
        self._table_features.setColumnCount(2)
        self._table_features.setHorizontalHeaderLabels(["特征名称", "特征值"])
        self._table_features.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table_features.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table_features.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_features.setAlternatingRowColors(True)
        self._table_features.verticalHeader().setDefaultSectionSize(22)
        self._populate_feature_table({})
        layout.addWidget(self._table_features)

        # 批量结果表格
        self._table_batch = QTableWidget()
        self._table_batch.setColumnCount(12)
        self._table_batch.setHorizontalHeaderLabels([
            "图片路径", "预测类别", "实际方法", "置信度",
            "green_ratio", "yellow_ratio", "dark_ratio",
            "H_mean", "S_mean", "V_mean",
            "glcm_contrast", "glcm_homogeneity",
        ])
        self._table_batch.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 12):
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

        # 摄像头信号
        self._btn_camera_open.clicked.connect(self._on_camera_open)
        self._btn_camera_close.clicked.connect(self._on_camera_close)
        self._btn_camera_pause.clicked.connect(self._on_camera_pause)
        self._btn_camera_screenshot.clicked.connect(self._on_camera_screenshot)

        # 分类方法切换时刷新模型元数据显示
        self._combo_method.currentIndexChanged.connect(self._on_method_changed)

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
            self._status_bar.showMessage(f"已选择图片：{file_path}")
            self._show_selected_image_preview(file_path)
            self._update_ui_state()

    def _show_selected_image_preview(self, image_path: str) -> None:
        """在打开图片后立即显示原图预览（尚未识别）。"""
        try:
            original = read_image(image_path)
            self._image_to_label(self._lbl_original, original)
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
                    method = "规则分类"  # 更新局部变量，供下方单图/批量分发使用
                    self._status_bar.showMessage("已切换为规则分类模式（模型文件不存在）")
                    # 不回退到 _do_single_recognition，而是 fall through 到下方的
                    # 单图/批量分发逻辑，确保批量模式下也能正确触发批量识别
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

    # ------------------------------------------------------------------
    # 摄像头实时识别
    # ------------------------------------------------------------------

    def _on_camera_open(self) -> None:
        """打开摄像头并启动实时识别。"""
        camera_id = self._spin_camera_id.value()
        camera_cfg = self._config.get("camera", {})

        # 如果已有摄像头打开，先关闭
        if self._camera_cap is not None:
            self._on_camera_close()

        # 尝试打开摄像头
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            QMessageBox.critical(
                self,
                "摄像头打开失败",
                f"无法打开摄像头设备 (index={camera_id})。\n"
                "请检查：\n"
                "  1. 摄像头是否被其他应用占用\n"
                "  2. 设备编号是否正确（尝试 0 或 1）\n"
                "  3. 摄像头驱动是否正常工作",
            )
            return

        # 设置分辨率
        width = camera_cfg.get("width", 1280)
        height = camera_cfg.get("height", 720)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self._camera_cap = cap
        self._camera_paused = False
        self._camera_frame = None
        self._last_inference_time = 0.0
        self._camera_fallback_msg = ""

        # 重置稳定性状态
        self._banana_votes = 0
        self._banana_confirmed = False
        self._proba_history.clear()

        # 清空 ML 模型缓存（允许用户切换方法后重新加载）
        self._model_cache.clear()

        # 启动摄像头刷新定时器
        fps = camera_cfg.get("display_fps", 30)
        interval_ms = max(1, int(1000 / fps))
        self._camera_timer = QTimer(self)
        self._camera_timer.timeout.connect(self._on_camera_tick)
        self._camera_timer.start(interval_ms)

        # 清除单图/批量状态
        self._current_image_path = None
        self._current_folder_path = None
        self._batch_results.clear()
        self._table_batch.setVisible(False)
        self._table_batch.setRowCount(0)

        # 初始化占位画面
        self._lbl_original.setPixmap(blank_placeholder("摄像头加载中..."))
        self._lbl_mask.setPixmap(blank_placeholder("等待推理..."))
        self._lbl_result.setPixmap(blank_placeholder("等待推理..."))

        self._update_camera_ui_state()
        self._update_ui_state()

        status_msg = f"摄像头已打开 (device={camera_id}, {width}×{height}) — 实时识别中..."
        stale_msg = self._check_model_staleness("KNN")
        if stale_msg:
            status_msg += f"  |  {stale_msg}"
        self._status_bar.showMessage(status_msg)

    def _on_camera_close(self) -> None:
        """关闭摄像头并释放资源。"""
        # 停止定时器
        if self._camera_timer is not None:
            self._camera_timer.stop()
            self._camera_timer.deleteLater()
            self._camera_timer = None

        # 释放摄像头
        if self._camera_cap is not None:
            self._camera_cap.release()
            self._camera_cap = None

        self._camera_frame = None
        self._camera_paused = False
        self._camera_fallback_msg = ""
        self._banana_votes = 0
        self._banana_confirmed = False
        self._proba_history.clear()
        self._model_cache.clear()

        # 恢复占位画面
        self._lbl_original.setPixmap(blank_placeholder("暂无图片"))
        self._lbl_mask.setPixmap(blank_placeholder("暂无数据"))
        self._lbl_result.setPixmap(blank_placeholder("暂无结果"))
        self._lbl_prediction.setText("—")
        self._lbl_advice.setText("—")
        self._lbl_ruleset.setText("")
        self._lbl_candidate_reason.setVisible(False)
        self._lbl_proba.setVisible(False)
        self._populate_feature_table({})

        self._update_camera_ui_state()
        self._status_bar.showMessage("摄像头已关闭")

    def _on_camera_pause(self) -> None:
        """暂停 / 继续实时画面。"""
        if self._camera_cap is None:
            return

        self._camera_paused = not self._camera_paused
        if self._camera_paused:
            self._btn_camera_pause.setText("▶ 继续")
            self._status_bar.showMessage("摄像头已暂停 — 点击「继续」恢复")
        else:
            self._btn_camera_pause.setText("⏸ 暂停")
            self._last_inference_time = 0.0  # 恢复时立即触发一次推理
            self._status_bar.showMessage("摄像头已恢复 — 实时识别中...")

    def _on_camera_screenshot(self) -> None:
        """截取当前帧并进行完整识别（使用当前选定的分类方法）。"""
        if self._camera_cap is None or self._camera_frame is None:
            QMessageBox.information(self, "提示", "请先打开摄像头并等待画面稳定。")
            return

        method = self._combo_method.currentText()

        # 检查 ML 模型文件
        if method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if not model_path.exists():
                reply = QMessageBox.question(
                    self,
                    "模型文件不存在",
                    f"模型文件 {model_path} 不存在。\n\n"
                    "是否回退到规则分类进行截图识别？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    method = "规则分类"
                    self._combo_method.setCurrentText("规则分类")
                else:
                    return

        self._status_bar.showMessage("正在识别截图...")
        QApplication.processEvents()

        try:
            result = run_inference_on_frame(
                self._camera_frame,
                self._config,
                method,
                self._model_cache,
            )
        except Exception as exc:
            QMessageBox.critical(self, "截图识别失败", f"推理过程出错：{exc}")
            self._status_bar.showMessage("截图识别失败")
            return

        prediction = result["prediction"]
        features = result["features"]
        processed = result["processed"]
        mask = result["mask"]
        method_used = result["method_used"]
        banana_detected = result.get("banana_detected", True)
        candidate_reason = result.get("candidate_reason", "")

        # 检查香蕉候选验证
        if not banana_detected:
            QMessageBox.information(
                self,
                "未检测到香蕉",
                f"当前画面中未检测到有效的香蕉区域。\n\n"
                f"原因：{candidate_reason}\n\n"
                "请确保香蕉在摄像头视野内且光照充足。",
            )
            self._status_bar.showMessage("截图识别：未检测到香蕉")
            return

        # 生成结果图
        result_img = draw_prediction(processed, mask, prediction,
                                     "" if method_used.startswith("规则分类") else method_used)

        # 缓存并显示
        self._current_original = self._camera_frame.copy()
        self._current_mask = mask
        self._current_result_img = result_img
        self._current_prediction = prediction
        self._current_features = {k: features.get(k, 0.0) for k in DISPLAY_FEATURES}
        self._display_results()

        self._status_bar.showMessage(
            f"截图识别完成 — 预测类别：{prediction}（方法：{method_used}）"
        )

    def _on_camera_tick(self) -> None:
        """摄像头定时器回调：抓取帧 → 显示 → 周期性推理。"""
        if self._camera_cap is None or not self._camera_cap.isOpened():
            return

        if self._camera_paused:
            return

        # 读取帧
        ret, frame = self._camera_cap.read()
        if not ret or frame is None:
            return

        # 镜像翻转
        if self._chk_mirror.isChecked():
            frame = cv2.flip(frame, 1)

        self._camera_frame = frame

        # 实时显示原始帧（按标签尺寸缩放）
        self._image_to_label(self._lbl_original, frame)

        # 推理节流：按 inference_interval_ms 间隔执行
        camera_cfg = self._config.get("camera", {})
        interval_s = camera_cfg.get("inference_interval_ms", 500) / 1000.0
        now = time.time()
        if now - self._last_inference_time >= interval_s:
            self._last_inference_time = now
            self._run_camera_inference(frame)

    def _run_camera_inference(self, frame: np.ndarray) -> None:
        """对当前帧运行推理流水线并更新 UI（含多帧稳定性投票）。"""
        method = self._combo_method.currentText()

        try:
            result = run_inference_on_frame(
                frame, self._config, method, self._model_cache,
            )
        except Exception:
            # 推理失败时静默跳过，下次 tick 重试
            return

        features = result["features"]
        processed = result["processed"]
        mask = result["mask"]
        banana_detected = result.get("banana_detected", False)
        candidate_reason = result.get("candidate_reason", "")

        # ---- 显示当前规则集名称 ------------------------------------------
        if self._config.get("camera_rules"):
            self._lbl_ruleset.setText("规则集: 摄像头规则 (camera_rules)")
        else:
            self._lbl_ruleset.setText("规则集: 静态规则 (rules)")

        # ---- 多帧稳定性投票 ----------------------------------------------
        stability_cfg = self._config.get("stability", {})
        confirm_frames = int(stability_cfg.get("confirm_frames", STABILITY_CONFIRM_FRAMES))
        lost_frames = int(stability_cfg.get("lost_frames", STABILITY_LOST_FRAMES))

        if banana_detected:
            self._banana_votes = min(self._banana_votes + 1, confirm_frames)
        else:
            # Decrement by ceil(confirm/lost) so that lost_frames consecutive
            # misses drop confirmation. E.g. confirm=4, lost=3 → step=2,
            # 2 misses drop from 4→2→0 (lose confirmation in ~lost_frames frames).
            step = max(1, int(math.ceil(confirm_frames / max(lost_frames, 1))))
            self._banana_votes = max(self._banana_votes - step, 0)

        # 确定当前稳定性状态（滞后：中间状态保持上一帧判定）
        if self._banana_votes >= confirm_frames:
            self._banana_confirmed = True
        elif self._banana_votes <= 0:
            self._banana_confirmed = False
        # else: 保持上一个状态

        # ---- 当前帧未检测到香蕉（候选验证失败）--------------------------
        if not banana_detected:
            self._lbl_mask.setPixmap(blank_placeholder("未检测到香蕉"))
            self._lbl_result.setPixmap(blank_placeholder("请将香蕉对准摄像头"))
            if self._banana_confirmed:
                # 已确认香蕉 → 短暂遮挡/丢失
                self._lbl_prediction.setText("⚠ 香蕉丢失")
                self._lbl_prediction.setStyleSheet(
                    "QLabel { color: #cc6600; font-weight: bold; }"
                )
                self._lbl_advice.setText(
                    f"请重新对准香蕉（{self._banana_votes}/{confirm_frames}）"
                )
            else:
                # 从未确认 → 无香蕉或正在寻找
                if self._banana_votes > 0:
                    self._lbl_prediction.setText("🔍 确认中...")
                    self._lbl_prediction.setStyleSheet(
                        "QLabel { color: #888888; font-weight: bold; }"
                    )
                    self._lbl_advice.setText(
                        f"正在确认香蕉...（{self._banana_votes}/{confirm_frames}）"
                    )
                else:
                    self._lbl_prediction.setText("未检测到香蕉")
                    self._lbl_prediction.setStyleSheet(
                        "QLabel { color: #888888; font-weight: bold; }"
                    )
                    self._lbl_advice.setText(
                        "请确保香蕉在画面中心区域，光照充足，背景简洁"
                    )
            # 显示候选验证失败原因
            if candidate_reason:
                self._lbl_candidate_reason.setText(f"原因: {candidate_reason}")
                self._lbl_candidate_reason.setVisible(True)
            else:
                self._lbl_candidate_reason.setVisible(False)
            # 仍显示实时特征值（方便调试分割效果）
            self._populate_feature_table(
                {k: features.get(k, 0.0) for k in DISPLAY_FEATURES}
            )
            self._lbl_proba.setVisible(False)
            return

        # ---- 当前帧检测到香蕉（候选验证通过）----------------------------
        self._lbl_candidate_reason.setVisible(False)
        self._lbl_proba.setVisible(False)

        # 香蕉确认中（票数不足）
        if not self._banana_confirmed:
            self._lbl_mask.setPixmap(blank_placeholder("确认中..."))
            self._lbl_result.setPixmap(blank_placeholder("请保持稳定"))
            self._lbl_prediction.setText("🔍 确认中...")
            self._lbl_prediction.setStyleSheet(
                "QLabel { color: #888888; font-weight: bold; }"
            )
            self._lbl_advice.setText(
                f"正在确认香蕉...（{self._banana_votes}/{confirm_frames}）"
            )
            self._populate_feature_table(
                {k: features.get(k, 0.0) for k in DISPLAY_FEATURES}
            )
            return

        # ---- 香蕉确认：显示成熟度结果 ------------------------------------
        prediction = result["prediction"]
        method_used = result["method_used"]
        proba = result.get("proba", {})

        # 检测是否发生 ML 回退（区分"模型问题回退"和"正常规则分类"）
        fallback_msg = ""
        is_low_confidence = False
        if method_used != method and method in METHOD_TO_MODEL:
            fallback_msg = f"（已回退: {method_used}）"
            is_low_confidence = True
        elif method_used.startswith("规则分类") and method != "规则分类":
            fallback_msg = f"（已回退: {method_used}）"
            is_low_confidence = True
        self._camera_fallback_msg = fallback_msg

        # 概率 / 置信度显示（含滑动窗口平滑）
        ml_cfg = self._config.get("ml", {})
        smooth_window = int(ml_cfg.get("smooth_window", 3))
        min_conf = float(ml_cfg.get("min_confidence", 0.55))
        # Resize deque to match configured window
        if self._proba_history.maxlen != max(smooth_window, 1):
            self._proba_history = deque(self._proba_history, maxlen=max(smooth_window, 1))

        if proba and method_used not in ("规则分类", "") and not method_used.startswith("规则分类"):
            # Push to sliding window and compute smoothed probabilities
            self._proba_history.append(dict(proba))
            smoothed: dict[str, float] = {}
            n = len(self._proba_history)
            for cls in ("unripe", "ripe", "overripe"):
                smoothed[cls] = sum(h.get(cls, 0.0) for h in self._proba_history) / n

            top_cls = max(smoothed, key=smoothed.get)
            top_conf = smoothed[top_cls]

            parts = [f"{cls}: {p:.1%}" for cls, p in sorted(smoothed.items(), key=lambda x: -x[1])]
            proba_line = f"置信度: {' | '.join(parts)}"
            if n > 1:
                proba_line += f" ({n}帧平滑)"

            # Low-confidence check: if top-1 below threshold, show rule-based reference
            if top_conf < min_conf:
                is_low_confidence = True
                rule_pred = features.get("rule_prediction", "unknown")
                proba_line += f"\n⚠ top-1 置信度 {top_conf:.1%} < 阈值 {min_conf:.0%}，规则分类参考: {rule_pred}"
                if not fallback_msg:
                    fallback_msg = f"（低置信: {top_conf:.1%} < {min_conf:.0%}）"
                self._camera_fallback_msg = fallback_msg

            self._lbl_proba.setText(proba_line)
            self._lbl_proba.setVisible(True)
        elif method_used not in ("规则分类", "") and not method_used.startswith("规则分类") and is_low_confidence:
            self._lbl_proba.setText(f"方法: {method_used}（低置信）")
            self._lbl_proba.setVisible(True)
        else:
            self._proba_history.clear()
            self._lbl_proba.setVisible(False)

        # 生成结果图
        label_suffix = ""
        if is_low_confidence:
            label_suffix = " [低置信]"
        result_img = draw_prediction(
            processed, mask, prediction,
            "" if method_used.startswith("规则分类") else method_used,
        )

        # 缓存并显示
        self._current_original = frame
        self._current_mask = mask
        self._current_result_img = result_img
        self._current_prediction = prediction
        self._current_features = {k: features.get(k, 0.0) for k in DISPLAY_FEATURES}

        # 更新 mask 和结果图（原图已在 tick 中更新）
        self._image_to_label(self._lbl_mask, mask, is_mask=True)
        self._image_to_label(self._lbl_result, result_img)

        # 预测 + 建议
        pred = prediction or "unknown"
        display_pred = f"{pred}{label_suffix}" if is_low_confidence else pred
        self._lbl_prediction.setText(display_pred)
        color = LABEL_COLORS.get(pred, LABEL_COLORS["unknown"])
        if is_low_confidence:
            self._lbl_prediction.setStyleSheet(
                f"QLabel {{ color: rgb({color[2]},{color[1]},{color[0]}); font-weight: bold; "
                "background-color: #fff3cd; padding: 2px; }}"
            )
        else:
            self._lbl_prediction.setStyleSheet(
                f"QLabel {{ color: rgb({color[2]},{color[1]},{color[0]}); font-weight: bold; }}"
            )
        advice = ADVICE.get(pred, ADVICE["unknown"])
        if fallback_msg:
            advice = f"{advice} {fallback_msg}"
        self._lbl_advice.setText(advice)

        # 特征表格
        self._populate_feature_table(self._current_features)

    def _check_model_staleness(self, method: str) -> str:
        """Check if the ML model is older than the feature CSV.

        Works for KNN, SVM, Logistic — looks up model path via METHOD_TO_MODEL
        and compares training data timestamp in model meta with the current
        ``combined_features.csv`` modification time.

        Returns an empty string if the model is up-to-date, or a warning
        message if the model should be re-trained.
        """
        if method not in METHOD_TO_MODEL:
            return ""
        model_filename = METHOD_TO_MODEL[method]
        model_path = self._model_dir / model_filename
        if not model_path.exists():
            return ""

        meta = load_model_meta(model_path)
        if meta is None:
            return ""

        feature_csv_mtime_str = meta.get("feature_csv_mtime")
        if not feature_csv_mtime_str:
            return ""

        try:
            model_train_time = datetime.fromisoformat(feature_csv_mtime_str)
        except (ValueError, TypeError):
            return ""

        # Check actual combined_features.csv modification time
        paths_cfg = self._config.get("paths", {})
        feature_csv_path = resolve_path(
            paths_cfg.get("feature_csv", "data/features/combined_features.csv")
        )
        if not feature_csv_path.exists():
            return ""

        csv_mtime = datetime.fromtimestamp(feature_csv_path.stat().st_mtime)
        if csv_mtime > model_train_time:
            csv_time_str = csv_mtime.strftime("%Y-%m-%d %H:%M")
            return (
                f"⚠ 特征表已更新 ({csv_time_str})，{method} 模型可能已过期。"
                "建议运行: python -m src.main_ml --config config.yaml"
            )

        return ""

    def _get_model_meta_text(self, method: str) -> str:
        """Return a human-readable summary of the model metadata for *method*.

        Returns an empty string when the model file is missing or the method
        is rule-based.
        """
        if method not in METHOD_TO_MODEL:
            return ""
        model_path = self._model_dir / METHOD_TO_MODEL[method]
        if not model_path.exists():
            return f"⚠ {method} 模型文件不存在"
        meta = load_model_meta(model_path)
        if meta is None:
            return f"{method} 模型已加载（无元数据）"

        parts = [f"{method} 模型"]
        classes = meta.get("classes", [])
        if classes:
            parts.append(f"类别: {', '.join(classes)}")
        n_samples = meta.get("n_samples")
        if n_samples:
            parts.append(f"样本数: {n_samples}")
        class_counts = meta.get("class_counts")
        if class_counts:
            cc_parts = [f"{c}={n}" for c, n in sorted(class_counts.items())]
            parts.append(f"分布: {', '.join(cc_parts)}")
        test_acc = meta.get("test_accuracy")
        if test_acc is not None:
            parts.append(f"测试准确率: {float(test_acc):.1%}")
        cv_acc = meta.get("cv_accuracy")
        if cv_acc is not None:
            parts.append(f"CV 准确率: {float(cv_acc):.1%}")
        train_time = meta.get("train_time")
        if train_time:
            parts.append(f"训练时间: {train_time}")

        return " | ".join(parts)

    def _run_multi_model_comparison(
        self, features: dict[str, float]
    ) -> dict[str, tuple[str, dict[str, float], str]]:
        """Run all four classification methods on the same features.

        Returns a dict mapping method name → (prediction, proba, method_used).
        Methods with missing or invalid models fall back gracefully.
        """
        results: dict[str, tuple[str, dict[str, float], str]] = {}
        cfg = self._config
        rules = cfg.get("rules", {})

        # Rule-based (always available)
        rule_pred = classify_by_rules(features, rules)
        results["规则分类"] = (rule_pred, {}, "规则分类")

        # ML methods
        for method in ["KNN", "SVM", "Logistic"]:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if not model_path.exists():
                fallback_pred = classify_by_rules(features, rules)
                results[method] = (fallback_pred, {},
                                   f"规则分类（{method} 模型不存在）")
                continue
            try:
                model = load_model(model_path)
                valid, reason = validate_model_classes(model)
                if not valid:
                    fallback_pred = classify_by_rules(features, rules)
                    results[method] = (fallback_pred, {},
                                       f"规则分类（{method} 类别不完整）")
                    continue
                pred, proba = predict_single(model, features)
                results[method] = (pred, proba, method)
            except Exception:
                fallback_pred = classify_by_rules(features, rules)
                results[method] = (fallback_pred, {},
                                   f"规则分类（{method} 异常回退）")

        return results

    def _update_camera_ui_state(self) -> None:
        """根据摄像头状态启用/禁用控件。"""
        camera_active = self._camera_cap is not None
        self._btn_camera_open.setEnabled(not camera_active)
        self._btn_camera_close.setEnabled(camera_active)
        self._btn_camera_pause.setEnabled(camera_active)
        self._btn_camera_screenshot.setEnabled(camera_active)
        self._spin_camera_id.setEnabled(not camera_active)

    def _on_method_changed(self, _index: int) -> None:
        """分类方法切换时刷新模型元数据显示和过期检查。"""
        method = self._combo_method.currentText()
        meta_text = self._get_model_meta_text(method)
        stale_msg = self._check_model_staleness(method) if method in METHOD_TO_MODEL else ""

        if meta_text:
            full = meta_text
            if stale_msg:
                full += f"  |  {stale_msg}"
            self._status_bar.showMessage(full)
        elif stale_msg:
            self._status_bar.showMessage(stale_msg)

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
        method_used = method  # track actual method (may differ on fallback)
        proba: dict[str, float] = {}
        proba_text = ""

        if method == "规则分类":
            prediction = row.get("rule_prediction", "unknown")
        else:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if model_path.exists():
                try:
                    model = load_model(model_path)
                    valid, reason = validate_model_classes(model)
                    if not valid:
                        QMessageBox.warning(
                            self,
                            "模型无效",
                            f"当前 {method} 模型类别不完整，无法用于预测。\n\n"
                            f"原因：{reason}\n\n"
                            "已自动回退到规则分类。\n"
                            f"请运行 python -m src.main_ml --config config.yaml 重新训练三分类模型。",
                        )
                        prediction = classify_by_rules(features, self._config.get("rules", {}))
                        method_used = f"规则分类（{method} 类别不完整）"
                    else:
                        prediction, proba = predict_single(model, features)
                        # 构建置信度文本
                        if proba:
                            parts = [f"{cls}: {p:.2%}" for cls, p in sorted(proba.items(), key=lambda x: -x[1])]
                            proba_text = " | ".join(parts)
                except Exception as exc:
                    QMessageBox.warning(self, "模型预测失败", f"ML 预测出错，回退到规则分类：{exc}")
                    prediction = classify_by_rules(features, self._config.get("rules", {}))
                    method_used = f"规则分类（{method} 异常回退）"
            else:
                prediction = row.get("rule_prediction", "unknown")
                method_used = f"规则分类（{method} 模型不存在）"
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
        # 静态图片模式显示规则集名称和方法信息
        self._lbl_ruleset.setText("规则集: 静态规则 (rules)")
        self._lbl_candidate_reason.setVisible(False)
        # 多模型对比（根据 ml.show_model_comparison 配置）
        ml_cfg = self._config.get("ml", {})
        show_comparison = bool(ml_cfg.get("show_model_comparison", False))
        if show_comparison:
            comparison = self._run_multi_model_comparison(features)
            comp_lines = ["多模型对比:"]
            for m_name, (m_pred, m_proba, m_used) in comparison.items():
                conf_str = ""
                if m_proba:
                    top_p = max(m_proba.values())
                    conf_str = f" ({top_p:.1%})"
                marker = " ◀" if m_name == method else ""
                comp_lines.append(f"  {m_name}: {m_pred}{conf_str} [{m_used}]{marker}")
            self._lbl_proba.setText("\n".join(comp_lines))
            self._lbl_proba.setVisible(True)
        elif proba_text:
            self._lbl_proba.setText(f"置信度: {proba_text}")
            self._lbl_proba.setVisible(True)
        else:
            self._lbl_proba.setVisible(False)

        # 模型过期检查（对所有 ML 方法）
        stale_msg = ""
        if method in METHOD_TO_MODEL:
            stale_msg = self._check_model_staleness(method)
        method_label = method_used if method_used != method else method
        status_text = f"识别完成 — 预测类别：{prediction}（方法：{method_label}）"
        if stale_msg:
            status_text += f"  |  {stale_msg}"
        self._status_bar.showMessage(status_text)

    def _do_batch_recognition(self) -> None:
        """启动批量识别线程。"""
        if not self._current_folder_path:
            return

        image_files = list_image_files(self._current_folder_path)
        if not image_files:
            QMessageBox.information(self, "提示", "所选文件夹中没有图片文件。")
            return

        method = self._combo_method.currentText()

        # 检查 ML 模型（存在性 + 类别完整性）
        if method in METHOD_TO_MODEL:
            model_path = self._model_dir / METHOD_TO_MODEL[method]
            if not model_path.exists():
                QMessageBox.warning(
                    self,
                    "模型文件不存在",
                    f"{method} 模型文件不存在，将回退到规则分类。\n"
                    f"请运行 python -m src.main_ml --config config.yaml 训练模型。",
                )
                self._combo_method.setCurrentText("规则分类")
                method = "规则分类"
            else:
                try:
                    model = load_model(model_path)
                    valid, reason = validate_model_classes(model)
                    if not valid:
                        QMessageBox.warning(
                            self,
                            "模型无效",
                            f"当前 {method} 模型类别不完整，无法用于预测。\n\n"
                            f"原因：{reason}\n\n"
                            "已自动回退到规则分类。\n"
                            f"请运行 python -m src.main_ml --config config.yaml 重新训练三分类模型。",
                        )
                        self._combo_method.setCurrentText("规则分类")
                        method = "规则分类"
                except Exception:
                    pass  # 加载失败时 BatchWorker 会进一步处理

        self._batch_results.clear()
        self._table_batch.setRowCount(0)
        self._table_batch.setVisible(True)

        self._btn_start.setEnabled(False)
        self._status_bar.showMessage(f"批量处理中... 0/{len(image_files)}")

        self._batch_method = method  # track for staleness check on finish
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

        # 置信度格式化（ML 方法时显示百分比，规则分类时显示 —）
        conf = result.get("confidence", 0.0)
        conf_text = f"{conf:.1%}" if conf > 0 else "—"

        columns = [
            result["image_path"],
            result["prediction"],
            result.get("method_used", result.get("method_requested", "—")),
            conf_text,
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
                    QApplication.palette().window().color()
                )
            self._table_batch.setItem(row_idx, col, item)

    def _on_batch_error(self, image_path: str, error: str) -> None:
        self._status_bar.showMessage(f"处理出错 ({Path(image_path).name}): {error}")

    def _on_batch_finished(self) -> None:
        self._btn_start.setEnabled(True)
        n = len(self._batch_results)
        if n > 0:
            self._btn_export.setStyleSheet(
                "QPushButton { background-color: #2ca02c; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #3cb03c; }"
            )
            self._btn_export.setToolTip(f"导出 {n} 条批量检测结果到 CSV 文件")
        # Model staleness check for the method used in this batch
        batch_method = getattr(self, "_batch_method", "")
        stale_msg = self._check_model_staleness(batch_method) if batch_method else ""
        status_text = f"批量处理完成 — 共处理 {n} 张图片"
        if stale_msg:
            status_text += f"  |  {stale_msg}"
        self._status_bar.showMessage(status_text)
        if n == 0:
            QMessageBox.information(self, "提示", "未成功处理任何图片。")

    def _on_export_csv(self) -> None:
        """导出批量结果到 CSV 文件。"""
        if not self._batch_results:
            QMessageBox.information(
                self,
                "无可导出结果",
                "当前没有批量检测结果可导出。\n\n"
                "操作步骤：\n"
                "  1. 点击「📁 选择文件夹」选择一个包含香蕉图片的文件夹\n"
                "  2. 选择分类方法（规则分类 / KNN / SVM / Logistic）\n"
                "  3. 点击「▶ 开始识别」执行批量检测\n"
                "  4. 批量完成后再次点击「💾 导出 CSV」\n\n"
                "提示：单图识别和摄像头截图不支持 CSV 导出。",
            )
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
                "method_requested", "method_used", "confidence",
                "prob_overripe", "prob_ripe", "prob_unripe",
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

    def _image_to_label(
        self,
        label: QLabel,
        image_bgr: np.ndarray | None,
        placeholder: str = "暂无图片",
        is_mask: bool = False,
    ) -> None:
        """Set a BGR image (or mask) onto a QLabel, scaled to fill the label.

        Uses the label's **current** size so images re-flow on window resize.
        """
        if label is None:
            return
        lbl_w = label.width()
        lbl_h = label.height()
        if lbl_w <= 4 or lbl_h <= 4:
            return  # not yet laid out

        target = min(lbl_w, lbl_h)

        if image_bgr is not None and image_bgr.size > 0:
            pixmap = (
                mask_to_qpixmap(image_bgr, target)
                if is_mask
                else cv_to_qpixmap(image_bgr, target)
            )
        else:
            pixmap = blank_placeholder(placeholder)
            pixmap = pixmap.scaled(
                lbl_w, lbl_h, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
        label.setPixmap(pixmap)

    def _refresh_image_labels(self) -> None:
        """Re-apply cached images to labels (called on window resize)."""
        self._image_to_label(self._lbl_original, self._current_original, "暂无图片")
        self._image_to_label(self._lbl_mask, self._current_mask, "暂无数据", is_mask=True)
        self._image_to_label(self._lbl_result, self._current_result_img, "暂无结果")

    def resizeEvent(self, event) -> None:  # noqa: N802
        """Window resize → re-fit images to their labels."""
        super().resizeEvent(event)
        self._refresh_image_labels()

    def closeEvent(self, event) -> None:  # noqa: N802
        """窗口关闭时释放摄像头资源。"""
        if self._camera_cap is not None:
            if self._camera_timer is not None:
                self._camera_timer.stop()
                self._camera_timer.deleteLater()
                self._camera_timer = None
            self._camera_cap.release()
            self._camera_cap = None
        super().closeEvent(event)

    def _update_ui_state(self) -> None:
        """根据当前模式启用/禁用控件。"""
        has_image = self._current_image_path is not None
        has_folder = self._current_folder_path is not None
        has_target = has_image or has_folder
        self._btn_start.setEnabled(has_target)

    def _display_results(self) -> None:
        """将当前缓存的识别结果显示到界面（使用标签当前尺寸缩放）。"""
        # 图像
        self._image_to_label(self._lbl_original, self._current_original, "暂无图片")
        self._image_to_label(self._lbl_mask, self._current_mask, "暂无数据", is_mask=True)
        self._image_to_label(self._lbl_result, self._current_result_img, "暂无结果")

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
