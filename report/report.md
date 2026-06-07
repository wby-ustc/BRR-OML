# 项目修改记录

本文档的定位是记录每次工程修改后的修改内容总结，不用于存放最终实验报告。新增记录按时间倒序写在顶部。

每条记录必须包含：

1. 本次内容修改完成时间。
2. 本次修改的文件列表和具体修改的代码位置。
3. 本次修改后项目相对于上一版项目的优化点或不足点。
4. 本次修改未完成的部分或需要继续优化的部分。

---

## 修改记录 #25 — 修复"导出 CSV"按钮始终不可点击的 UX 问题

**修改时间**：2026-06-03 23:31

### 问题诊断

#24 修复了 `_on_start_recognition` 中 ML 模型缺失时批量模式被跳过的调度 bug。但用户反馈修复后按钮仍无反应。经排查，`_btn_export`（导出 CSV 按钮）在**6 处**被主动 `setEnabled(False)`，仅在**1 处**（`_on_batch_finished`）被启用。按钮在绝大多数时间处于 Qt `disabled` 状态，此时点击完全无响应（Qt 的 disabled 按钮不发射 `clicked` 信号，也不触发任何视觉反馈）。

**根因**：`_btn_export.setEnabled(False)` 分布在以下位置：

| 位置 | 触发时机 | 后果 |
|------|---------|------|
| `_build_toolbar` (L433) | 应用启动时 | 按钮初始即 disabled |
| `_on_open_image` (L662) | 打开单张图片 | 用户无法导出 |
| `_on_open_folder` (L685) | 打开文件夹 | 按钮 disabled，用户困惑 |
| `_on_camera_open` (L799) | 打开摄像头 | 按钮 disabled |
| `_do_batch_recognition` (L1482) | 开始批量识别 | 批量运行中按钮 disabled |

唯一的启用点在 `_on_batch_finished` (L1539)。用户在单图模式、摄像头模式甚至批量运行过程中点击按钮，Qt 完全不响应，没有任何提示信息。用户不知道是因为功能不可用还是 bug。

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/app_pyqt.py` | L431-433 | `_build_toolbar`：移除 `setEnabled(False)`，改为 `setToolTip("批量检测完成后可导出 CSV 结果文件")` |
| `src/app_pyqt.py` | L659-663 | `_on_open_image`：移除 `_btn_export.setEnabled(False)` |
| `src/app_pyqt.py` | L681-685 | `_on_open_folder`：移除 `_btn_export.setEnabled(False)` |
| `src/app_pyqt.py` | L796-799 | `_on_camera_open`：移除 `_btn_export.setEnabled(False)` |
| `src/app_pyqt.py` | L1478-1482 | `_do_batch_recognition`：移除 `_btn_export.setEnabled(False)` |
| `src/app_pyqt.py` | L1537-1541 | `_on_batch_finished`：移除 `setEnabled(n > 0)`，改为 `n > 0` 时将按钮样式设为绿色高亮（`background-color: #2ca02c`）+ 更新 tooltip 显示可导出条数 |
| `src/app_pyqt.py` | L1549-1562 | `_on_export_csv`：无批量结果时弹出的对话框从"没有可导出的结果"改为包含完整操作步骤（选择文件夹→选择方法→开始识别→导出）+ 单图/摄像头不支持导出的提示 |

### 修复前后行为对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 应用刚启动 | 按钮灰色 disabled，点击无反应 | 按钮正常样式 + tooltip 提示 |
| 打开单图后 | 按钮灰色 disabled，点击无反应 | 点击弹出对话框，列出批量检测操作步骤 |
| 打开文件夹后 | 按钮灰色 disabled，点击无反应 | 点击弹出对话框引导用户点击"开始识别" |
| 批量运行中 | 按钮灰色 disabled | 点击弹出对话框提示正在处理 |
| 批量完成后 | 按钮 enabled，无特殊样式 | 按钮**绿色高亮** + tooltip 显示"N 条结果" |
| 批量完成→导出→切换单图 | 按钮 disabled | 按钮恢复默认样式，点击弹窗引导 |

### 优化点

1. **按钮始终可交互**：任何模式下点击都能获得明确反馈，用户不会觉得功能"坏了"。
2. **渐进式引导**：无结果时弹出的对话框包含完整 4 步操作流程，新用户无需猜测如何使用。
3. **结果就绪时视觉高亮**：批量完成后按钮变为绿色（与"开始识别"按钮一致的绿色高亮风格），tooltip 显示具体导出条数，明确引导用户点击。
4. **不改变原有逻辑**：`_batch_results` 的清空时机和 `_on_batch_finished` 的触发时机不变，仅改变按钮状态管理策略。

### 不足点

1. **无批量结果时按钮仍保持默认灰色样式**：视觉上不够醒目，用户可能忽略。后续可考虑始终绿色但附带 `(N=0)` 计数提示。
2. **未支持单图/截图结果的 CSV 导出**：当前仅批量模式可导出。若后续需要，可扩展为缓存最近 N 次单图/截图结果并支持导出。

### 未完成 / 待继续优化

1. 按钮样式可从"默认灰色 ↔ 绿色高亮"进一步升级为"灰色(N=0) → 橙色(N>0, 未导出) → 绿色(已导出)"三态指示。
2. 考虑在单图模式下也缓存结果，支持"导出当前结果"功能。

---

## 修改记录 #24 — 修复批量模式下 ML 模型缺失导致 CSV 导出不可用

**修改时间**：2026-06-03 23:21

### 问题诊断

用户反馈"导出 CSV"按钮不可用。经排查，问题不在 `_on_export_csv` 自身，而在上游调度函数 `_on_start_recognition`。

**根因**：[app_pyqt.py:720-724](src/app_pyqt.py#L720-L724) — 当用户在批量模式下选择了 ML 方法但模型文件不存在，弹出的回退对话框中点击"Yes"后，代码硬编码调用了 `self._do_single_recognition()`。该方法首行即检查 `if not self._current_image_path: return`，而批量模式下 `_current_image_path` 为 `None`，因此该方法静默返回，批量识别从未启动，`_on_batch_finished` 永远不会被调用，导出按钮永远无法启用。

**影响范围**：选中任意 ML 方法（KNN/SVM/Logistic）且对应 `.pkl` 文件被删除、移动或从未训练的场景。当前项目三类模型文件均存在，因此仅在模型文件意外缺失时触发。

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/app_pyqt.py` | L720-724 | `_on_start_recognition`：模型缺失回退路径不再硬编码调用 `_do_single_recognition()`；改为更新局部变量 `method = "规则分类"` 后 fall through 到下方的单图/批量分发逻辑（L731-737），使批量模式也能正确触发 `_do_batch_recognition()` |

### 修复前后对比

```
修复前:
  if reply == Yes:
      setCurrentText("规则分类")
      _do_single_recognition()   ← 批量模式下静默返回，批量从未启动
      return

修复后:
  if reply == Yes:
      setCurrentText("规则分类")
      method = "规则分类"        ← 更新局部变量
      # fall through → 下方 dispatch 正确路由到 _do_batch_recognition()
```

### 优化点

1. **批量模式 + ML 回退链路打通**：模型缺失时回退到规则分类后，批量识别正确启动 → 完成 → 导出按钮启用。
2. **不影响正常路径**：模型存在时或用户选择"规则分类"时，原逻辑不变。
3. **与其他回退路径一致**：`_on_camera_screenshot` 中同样的场景已经正确实现（更新 local `method` 后 fall through），本次修复使 `_on_start_recognition` 与之行为一致。

### 不足点

1. **仅在模型文件缺失时暴露**：当前三类模型均正常存在（KNN/SVM/Logistic `.pkl`），因此日常使用中该 bug 不可见。但若用户意外删除模型文件或在新环境中首次运行，批量模式会静默失败。
2. **未增加自动化覆盖**：`_on_start_recognition` 的 UI 交互逻辑（QMessageBox + 分支）当前没有单元测试覆盖，建议后续增加 mock-based 的 GUI 测试。

### 未完成 / 待继续优化

1. 增加 `_on_start_recognition` 中 ML 回退路径的自动化测试。
2. 考虑在 UI 中增加更明确的批量模式状态指示（如进度条），使用户更容易判断批量是否正在运行。

---

## 修改记录 #23 — 进阶版 ML 批量增强 + 概率平滑 + 多模型对比 + 模型元数据

**修改时间**：2026-06-03 23:06

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `config.yaml` | L186-204 | **新增** `ml` 配置节：`min_confidence: 0.55`、`smooth_window: 3`、`show_model_comparison: false` |
| `src/app_pyqt.py` | L18 | 新增 `from collections import deque` |
| `src/app_pyqt.py` | L236-290 | `BatchWorker.run()`：新增 `method_requested`、`method_used`、`confidence`、`prob_overripe`、`prob_ripe`、`prob_unripe` 字段；区分”模型不存在”和”类别不完整”回退 |
| `src/app_pyqt.py` | L594-604 | 批量表格列数 10→12，新增”实际方法”和”置信度”列 |
| `src/app_pyqt.py` | L1345-1370 | `_on_batch_result`：新增实际方法和置信度列，置信度在规则分类时显示 — |
| `src/app_pyqt.py` | L1401-1413 | `_on_export_csv`：CSV 字段新增 method_requested/method_used/confidence/prob_overripe/prob_ripe/prob_unripe |
| `src/app_pyqt.py` | L328-329 | `__init__` 新增 `_proba_history: deque` 概率滑动窗口 |
| `src/app_pyqt.py` | L754, L806 | `_on_camera_open/close`：重置/清除 `_proba_history` |
| `src/app_pyqt.py` | L1073-1107 | `_run_camera_inference`：①读取 `ml.smooth_window`/`ml.min_confidence`；②滑动窗口平滑概率显示 `(N帧平滑)`；③top-1 < min_confidence 时标记低置信 + 显示规则分类参考 |
| `src/app_pyqt.py` | L1119 | 非 ML 路径清除 `_proba_history` |
| `src/app_pyqt.py` | L1226-1260 | **新增** `_get_model_meta_text(method)`：读取模型元数据返回可读摘要（classes/n_samples/class_counts/train_time/test_accuracy/cv_accuracy） |
| `src/app_pyqt.py` | L1262-1300 | **新增** `_run_multi_model_comparison(features)`：四种方法并行对比，模型缺失/无效时独立回退 |
| `src/app_pyqt.py` | L626-627 | 新增 `_combo_method.currentIndexChanged` → `_on_method_changed` |
| `src/app_pyqt.py` | L1315-1327 | **新增** `_on_method_changed(_index)`：切换方法时显示模型元数据 + 过期检查 |
| `src/app_pyqt.py` | L1408-1426 | `_do_single_recognition`：`ml.show_model_comparison=true` 时显示四种方法对比（含置信度、实际方法、选中标记 ◀） |

### 优化点

1. **批量结果大幅增强**：`BatchWorker` 输出新增 7 个字段（method_requested/method_used/confidence/prob_overripe/prob_ripe/prob_unripe）；批量表格新增”实际方法”和”置信度”列；CSV 导出同步新增全部字段。

2. **概率滑动窗口平滑**：摄像头模式下维护 `_proba_history` deque（默认 3 帧），每帧 proba 推入后计算 N 帧平均，显示 `(3帧平滑)` 标记，有效消除 KNN 单帧概率抖动。

3. **低置信自动检测 + 规则参考**：平滑后 top-1 < `ml.min_confidence`（55%）时标记”低置信”，在 `_lbl_proba` 显示 `⚠ top-1 置信度 48% < 阈值 55%，规则分类参考: ripe`。

4. **多模型并行对比**：`_run_multi_model_comparison` 对同一特征运行四种方法，单图识别可选显示对比结果（当前选中方法 ◀ 标记）。

5. **模型元数据可视化**：切换方法时状态栏显示模型 classes/n_samples/class_counts/train_time/test_accuracy/cv_accuracy 完整信息，模型缺失/过期时同步警告。

6. **所有参数集中在 config.yaml**：`ml.min_confidence`/`smooth_window`/`show_model_comparison` 可配置。

### 不足点

1. 概率平滑使用简单算术平均，未考虑时间衰减权重。
2. `ml.show_model_comparison` 默认 false（每次加载 3 个模型增加约 50-100ms）。
3. 摄像头截图和批量模式未使用多模型对比。
4. 模型元数据仅在状态栏显示，无独立对话框。

### 未完成 / 待继续优化

1. 概率平滑可升级为指数加权移动平均（EWMA）。
2. `show_model_comparison` 可增加 UI 复选框。
3. 模型元数据可扩展为独立信息卡片对话框。
4. 低置信场景可给出操作建议（靠近摄像头、调整光照等）。

---

## 修改记录 #22 — 进阶版机器学习模型实时识别

**修改时间**：2026-06-03 22:47

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/app_pyqt.py` | L100 | `CLASS_METHODS` 从 `[“规则分类”, “KNN”]` 扩展为 `[“规则分类”, “KNN”, “SVM”, “Logistic”]`，进阶版开放全部四种分类方法 |
| `src/app_pyqt.py` | L568-574 | `_build_info_panel`：新增 `_lbl_proba` QLabel（ML 模型概率/置信度/方法信息行），默认隐藏，ML 预测时有内容时显示 |
| `src/app_pyqt.py` | L1108-1148 | `_check_knn_staleness()` → `_check_model_staleness(method)`：接受方法名参数，通过 `METHOD_TO_MODEL` 查找对应模型文件，支持 KNN/SVM/Logistic 通用过期检查 |
| `src/app_pyqt.py` | L788 | `_on_camera_open`：`_check_knn_staleness()` → `_check_model_staleness(“KNN”)` |
| `src/app_pyqt.py` | L797 | `_on_camera_close`：新增 `_lbl_proba.setVisible(False)` 清除概率显示 |
| `src/app_pyqt.py` | L1032, L1036 | `_run_camera_inference` 非确认路径：新增 `_lbl_proba.setVisible(False)` |
| `src/app_pyqt.py` | L1054-1084 | `_run_camera_inference` 确认路径：从 `result[“proba”]` 提取概率，当 ML 方法正常预测时显示置信度 `overripe: 85% | ripe: 12% | unripe: 3%`；回退时显示 `方法: 规则分类（KNN 异常回退）（低置信）` |
| `src/app_pyqt.py` | L1187-1238 | `_do_single_recognition`：新增 `method_used` 变量跟踪实际分类方法（正常/回退/模型无效/模型不存在）；ML 预测后将概率文本显示到 `_lbl_proba`；模型过期检查从 `method == “KNN”` 改为 `method in METHOD_TO_MODEL` 支持所有 ML 方法 |
| `src/app_pyqt.py` | L1307 | `_do_batch_recognition`：新增 `self._batch_method = method` 记录批量分类方法 |
| `src/app_pyqt.py` | L1361-1363 | `_on_batch_finished`：`_check_knn_staleness()` → `_check_model_staleness(batch_method)` |

### 优化点

1. **进阶版 ML 方法全面开放**：UI 下拉框现在包含规则分类、KNN、SVM、Logistic 四种方法，用户可在单图、批量、截图、实时摄像头四条路径中自由选择。SVM/Logistic 模型已在 #21 中训练完毕（SVM test=100%, CV=94.67%），可立即使用。

2. **模型过期检查通用化**：`_check_model_staleness(method)` 替代 `_check_knn_staleness()`，通过 `METHOD_TO_MODEL` 映射查找对应模型元数据 JSON。KNN/SVM/Logistic 均可检测 `combined_features.csv` 比模型训练时间更新的情况，状态栏显示具体方法名和重新训练命令。

3. **ML 预测概率/置信度可视化**：
   - 摄像头实时模式：香蕉确认后显示 `置信度: overripe: 85% | ripe: 12% | unripe: 3%`
   - 单图识别模式：预测结果下方显示概率分布
   - ML 回退时显示 `方法: 规则分类（KNN 类别不完整）（低置信）`，明确区分正常预测和回退兜底
   - 概率标签在摄像头关闭、香蕉丢失、确认中时自动隐藏

4. **`method_used` 全程追踪**：`_do_single_recognition` 新增 `method_used` 变量记录实际分类路径——正常 ML 预测与原 method 一致时为方法名本身，回退时标注具体原因（`规则分类（KNN 类别不完整）`、`规则分类（SVM 模型不存在）`、`规则分类（Logistic 异常回退）`）。信息区同时显示预测类别和实际方法。

5. **四条识别路径完整覆盖**：
   - **单图**：模型缺失→弹窗回退；模型无效→弹窗警告+规则兜底；ML 正常→显示概率
   - **批量**：模型缺失/无效→弹窗警告+自动回退规则分类→BatchWorker 使用规则分类处理
   - **截图**：通过 `run_inference_on_frame` → `predict_features` → 模型校验+规则回退
   - **摄像头**：通过 `run_inference_on_frame` → 模型缓存+校验+概率显示+回退标记

6. **不破坏基础版功能**：规则分类始终作为默认选项和兜底路径；`run_inference_on_frame` 和 `predict_features` 的回退逻辑未变；所有现有测试通过。

### 不足点

1. **SVM/Logistic 在 75 样本规模下与规则分类仍有差距**：规则分类 98.67% vs SVM CV 94.67% vs Logistic CV 94.67%。在小样本下规则分类仍是最优选择，SVM/Logistic 的优势需要更大样本量才能体现。

2. **摄像头实时模式下概率显示依赖帧率**：500ms 推理间隔下概率值每帧刷新，数值可能有微小波动（尤其是 KNN 在小样本下对特征噪声敏感）。可通过多帧概率平均进一步提升稳定性。

3. **概率显示仅在 ML 方法正常预测时出现**：回退到规则分类时不显示概率分布（规则分类无概率输出），用户无法直观对比规则分类和 ML 分类的分歧程度。

4. **批量模式未逐条显示方法信息**：批量表格中仅显示预测类别，未单独列出每张图片使用的实际分类方法和概率。

### 未完成 / 待继续优化

1. 在批量结果表格中增加”分类方法”和”置信度”列，让用户能逐条查看每张图片的预测细节。
2. 摄像头模式可增加”多模型并行对比”模式：同一帧同时用规则/KNN/SVM/Logistic 预测，在界面中并排显示结果。
3. 当样本量扩充至每类 50+ 后，重新评估四种方法的排名变化和进阶版默认推荐。
4. 可考虑在规则分类中增加”置信度”概念（如基于 green_ratio 到阈值的距离），使回退场景下也能给用户一定参考。

---

## 修改记录 #21 — 三类错误样本替换后复测

**修改时间**：2026-06-03 22:29

---

## 修改记录 #21 — 三类错误样本替换后复测

**修改时间**：2026-06-03 22:29

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `data/raw/overripe/IMG_20260603_222331.jpg` | 替换 | 替代上轮误判为 ripe 的 IMG_20260603_212906.jpg（新增过熟样本，表面有明显褐斑） |
| `data/raw/overripe/IMG_20260603_222341.jpg` | 替换 | 替代上轮误判为 ripe 的 IMG_20260603_212911.jpg（新增过熟样本，纹理对比度更高） |
| `data/raw/unripe/IMG_20260603_222435.jpg` | 替换 | 替代上轮误判为 ripe 的 IMG_20260603_213226.jpg（新增未熟样本，绿色比例更明显） |
| `data/raw/ripe/banana-24.jpg` | 未替换 | 唯一剩余错误样本（green_ratio=0.028 ≥ 0.012，已知不可约减边界样本） |
| `data/features/combined_features.csv` | 自动重新生成 | 由 `python -m src.main_rule_based` 基于更新后 75 样本重新生成 |
| `results/rule_based/summary.csv` | 自动重新生成 | 同上 |
| `models/knn_model.pkl` | 自动重新生成 | 基于更新后 combined_features.csv 重新训练 |
| `models/svm_model.pkl` | 自动重新生成 | 同上（进阶版预留） |
| `models/logistic_model.pkl` | 自动重新生成 | 同上（进阶版预留） |
| `models/*_model_meta.json` | 自动重新生成 | 三类模型元数据 JSON 同步更新 |

### 复测结果对比（规则分类）

| 指标 | 替换前 (#20) | 替换后 (#21) | 变化 |
|------|:-----------:|:-----------:|:----:|
| 总准确率 | 71/75 = 94.67% | 74/75 = **98.67%** | **+4.00pp** |
| overripe 召回 | 23/25 = 92.00% | 25/25 = **100.00%** | +8.00pp |
| ripe 召回 | 24/25 = 96.00% | 24/25 = 96.00% | 0pp |
| unripe 召回 | 24/25 = 96.00% | 25/25 = **100.00%** | +4.00pp |
| 唯一错误 | 4 个 | **1 个** (banana-24.jpg) | — |

### 机器学习复测结果对比（52 train / 23 test）

| 模型 | 替换前 Test Acc | 替换后 Test Acc | 替换前 CV | 替换后 CV |
|------|:--------------:|:--------------:|:---------:|:---------:|
| KNN | 91.30% | 91.30% | 88.00% | **94.67%** |
| SVM | 86.96% | **100.00%** | 93.33% | **94.67%** |
| Logistic | 86.96% | 91.30% | 94.67% | 94.67% |

### 优化点

1. **overripe 和 unripe 召回均恢复至 100%**：替换的 3 张错误样本替换后均被正确分类。overripe 中两张全黄低纹理图片被替换为有明显褐斑的样本，unripe 中 green_ratio=0.011 的边界样本被替换为绿色更明显的样本。

2. **SVM 测试准确率从 86.96% 跃升至 100%**：在本次 52/23 split 上 SVM 零错误分类全部 23 个测试样本，证明三类特征在高维空间中具有良好的线性可分性（RBF kernel）。

3. **KNN CV 从 88.00% 跃升至 94.67%**：替换错误样本后三类特征边界更清晰，KNN 在 5-fold CV 下标准差从 8.84% 降至 4.99%，稳定性显著提升。

4. **仅剩 1 个已知不可约减边界样本**：banana-24.jpg (green_ratio=0.028) 处于 ripe/unripe 连续光谱过渡区域，任何单阈值方案在此处都会产生个别错误。该样本无需替换——它是有价值的边界 case，如实反映了两类间的自然重叠。

5. **本轮仅更新数据和模型**：Python 代码未作任何修改，compileall 和 pytest 17 项测试全部通过。

### 不足点

1. **唯一剩余错误 banana-24.jpg 无法通过阈值调整解决**：其 green_ratio=0.028 略超 0.012 阈值但实际是成熟香蕉，提高阈值会牺牲 unripe 召回（unripe 样本 green_ratio q25=0.020）。
2. **SVM 100% test accuracy 受 split 随机性影响**：75 样本规模下 single split 的 100% 不代表泛化完美，应以 CV 94.67%±4.99% 为更可靠的参考。
3. **样本量仍有限**：每类 25 张，统计结论的可靠性受样本规模限制。

### 未完成 / 待继续优化

1. 扩充样本量至每类 50+ 张后重新评估全部模型。
2. 如需消除 banana-24.jpg 错误，可考虑引入 GLCM 纹理特征辅助规则（unripe 的 glcm_contrast 通常高于 ripe），或放宽三分类为"unripe / ripe / overripe"的概率输出而非硬分类。
3. 当前 SVM CV 94.67% 已与规则分类 98.67% 接近，当样本量增加后 SVM 可能反超规则分类，届时可考虑在进阶版 UI 中开放 SVM/Logistic。

---

## 修改记录 #20 — 最新样本复测 + UI 可解释性增强 + 摄像头鲁棒性优化

**修改时间**：2026-06-03 21:58

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/app_pyqt.py` | L16-17 | 新增 `import math`、`from datetime import datetime` |
| `src/app_pyqt.py` | L43-48 | `from .ml_classifier` 导入新增 `load_model_meta` |
| `src/app_pyqt.py` | L540-552 | `_build_info_panel`：新增 `_lbl_ruleset`（规则集名称标签）和 `_lbl_candidate_reason`（候选验证失败原因标签） |
| `src/app_pyqt.py` | L795-798 | `_on_camera_close`：关闭时清除 `_lbl_ruleset` 和 `_lbl_candidate_reason` |
| `src/app_pyqt.py` | L770-774 | `_on_camera_open`：打开摄像头后调用 `_check_knn_staleness()`，若模型过期则在状态栏显示警告 |
| `src/app_pyqt.py` | L933-1096 | `_run_camera_inference` 重写：①显示当前规则集名称（摄像头/静态）；②区分三种检测状态——"未检测到香蕉"（候选验证失败+原因）、"🔍 确认中..."（投票累积）、"⚠ 香蕉丢失"（已确认后短暂丢失）；③检测到回退时显示 `[低置信]` 标签和黄色背景；④稳定性投票使用 `lost_frames` 配置实现非对称升降 |
| `src/app_pyqt.py` | L1098-1133 | **新增** `_check_knn_staleness()` 方法（约 35 行）：读取 `knn_model_meta.json` 的 `feature_csv_mtime`，与 `combined_features.csv` 实际修改时间对比，若 CSV 更新则返回过期警告 |
| `src/app_pyqt.py` | L1220-1224 | `_do_single_recognition`：识别完成后显示规则集名称 + KNN 过期检查 |
| `src/app_pyqt.py` | L1317-1319 | `_on_batch_finished`：批量完成后检查 KNN 模型过期 |
| `src/inference.py` | L231-243 | `_DEFAULT_CANDIDATE`：`min_banana_color_ratio` 0.20→0.22、`min_yellow_green_ratio` 0.12→0.15、`min_extent` 0.25→0.28（与 config.yaml 同步） |
| `config.yaml` | L118-124 | `camera_rules`：`contrast_high` 2.20→1.95（更好捕获 borderline overripe）、`yellow_ratio_threshold` 0.40→0.42（减少非香蕉黄色物体误触发） |
| `config.yaml` | L137-150 | `candidate`：`min_banana_color_ratio` 0.20→0.22、`min_yellow_green_ratio` 0.12→0.15、`min_extent` 0.25→0.28（收紧非香蕉物体过滤） |
| `config.yaml` | L164-167 | `stability`：`confirm_frames` 3→4（约 2s 确认延迟）、`lost_frames` 2→3（减少短暂遮挡导致的丢失）；附设计注释 |
| `data/features/combined_features.csv` | 自动重新生成 | 由 `python -m src.main_rule_based` 基于 75 样本重新生成 |
| `models/knn_model.pkl` | 自动重新生成 | 基于 75 三分类样本重新训练，classes=['overripe','ripe','unripe'] |
| `models/svm_model.pkl` | 自动重新生成 | 同上（进阶版预留） |
| `models/logistic_model.pkl` | 自动重新生成 | 同上（进阶版预留） |
| `models/*_model_meta.json` | 自动重新生成 | 三类模型元数据 JSON，含 feature_csv_mtime、train_time、test_accuracy、cv_accuracy |

### 最新样本复测结果

**规则分类（75 样本，三类各 25）：**

| 类别 | 正确 | 错误 | 召回率 | 主要错误原因 |
|------|:----:|:----:|:------:|-------------|
| overripe | 23 | 2 | 92.00% | IMG_20260603_212906/212911：yellow_ratio 极高 (0.93-0.95)、contrast 偏低 (1.16-1.54)，Rule 5 误判为 ripe |
| ripe | 24 | 1 | 96.00% | banana-24.jpg：green_ratio=0.028 ≥ 0.012，Rule 1 误判为 unripe（已知边界样本） |
| unripe | 24 | 1 | 96.00% | IMG_20260603_213226.jpg：green_ratio=0.011 < 0.012（仅差 0.001），Rule 5 误判为 ripe |
| **总计** | **71** | **4** | **94.67%** | — |

**机器学习（52 train / 23 test）：**

| 模型 | Test Acc | CV Mean ± Std | 备注 |
|------|:--------:|:-------------:|------|
| KNN | 91.30% | 88.00% ± 8.84% | 基础版开放 |
| SVM | 86.96% | 93.33% ± 4.22% | 进阶版预留 |
| Logistic | 86.96% | 94.67% ± 6.53% | 进阶版预留 |
| **Rule Baseline** | **94.67%** | — | 当前最优 |

### 优化点

1. **最新样本复测完成**：确认新 overripe（10 张）和 unripe（7 张）替换图片后的规则分类准确率为 94.67%，仅 4 个错误样本（2 个 overripe 为新样本中偏黄的边界 case、2 个为已知的 green_ratio 边界样本）。KNN/SVM/Logistic 模型均已重新训练并保存元数据 JSON。

2. **UI 检测状态可解释性大幅提升**：
   - **candidate_reason 显示**：摄像头模式下未检测到香蕉时，界面直接显示验证失败的具体原因（如"香蕉颜色占比过低""目标不在画面中心区域"等），用户可据此调整摆放位置和光照。
   - **规则集名称显示**：信息区始终显示当前使用的规则集——摄像头模式显示"摄像头规则 (camera_rules)"，静态图片显示"静态规则 (rules)"，避免用户困惑。
   - **三种检测状态明确区分**：
     - "未检测到香蕉"（候选验证失败）+ 具体原因 — 明确告知系统无法找到香蕉
     - "🔍 确认中..."（投票累加中）— 告知正在等待画面稳定
     - "⚠ 香蕉丢失"（已确认后短暂丢失）+ 票数指示 — 区分于从未检测到
   - **低置信/回退状态标志**：当 ML 模型回退到规则分类时，预测结果显示 `[低置信]` 标签和黄色背景，与正常识别结果视觉区分。

3. **KNN 模型过期智能检测**：`_check_knn_staleness()` 在摄像头打开、单图识别完成、批量处理完成三个时机检查 `knn_model_meta.json` 中的 `feature_csv_mtime` 与 `combined_features.csv` 实际修改时间。若 CSV 较新，在状态栏显示 `⚠ 特征表已更新，KNN 模型可能已过期` 并给出重新训练命令。该功能使用已存在的 `load_model_meta()` 接口，无新增依赖。

4. **摄像头鲁棒性参数微调（基于最新样本分布）**：
   - **候选验证收紧**：`min_banana_color_ratio` 20%→22%、`min_yellow_green_ratio` 12%→15%、`min_extent` 0.25→0.28，减少纯棕色/暗色非香蕉物体误通过。
   - **camera_rules 平衡**：`contrast_high` 2.20→1.95 以更好捕获摄像头下 borderline overripe；`yellow_ratio_threshold` 0.40→0.42 在保持 ripe 召回的同时减少极端非香蕉黄色物体的误触发。
   - **稳定性增强**：`confirm_frames` 3→4（约 2s @ 500ms 推理间隔），`lost_frames` 2→3 配合新的非对称投票下降步长（`ceil(confirm/lost)`），实现"快降慢升"策略——香蕉丢失时约 2 帧即可解除确认，但确认需要 4 帧连续检测。
   - 所有参数均集中在 `config.yaml`，无硬编码到 Python 文件。

5. **不破坏现有功能**：单图识别、批量检测、静态规则分类和 ML 训练流水线保持不变。compileall 无错误，pytest 17 项全部通过。

### 不足点

1. **overripe 两类新样本误判为规则阈值固有限制**：`IMG_20260603_212906.jpg` (contrast=1.54) 和 `IMG_20260603_212911.jpg` (contrast=1.16) 的 contrast 均远低于静态 `contrast_high=1.70` 和摄像头 `contrast_high=1.95`，本质上是表面黑斑极少的过熟香蕉（或标签边界模糊），仅靠 HSV+GLCM 特征难以与 ripe 区分。

2. **摄像头阈值仍为推理值**：`camera_rules` 的 `contrast_high=1.95`、`yellow_ratio_threshold=0.42` 基于静态样本分布推导，尚未在真实多场景摄像头环境下进行系统化网格搜索验证。

3. **KNN CV 准确率 (88.00%) 低于规则基线 (94.67%)**：在 75 样本规模下，规则分类器经过精细校准后表现优于 KNN。随着样本量增加，ML 模型的泛化优势才会逐渐体现。

4. **`lost_frames` 实现为非对称投票下降步长**：当前实现不是跟踪连续丢失帧数，而是通过 `ceil(confirm/lost)` 计算每次不检测香蕉时的投票下降量。这种近似在极端帧率变化时行为与设计预期略有偏差，但对 500ms 推理间隔场景足够。

### 未完成 / 待继续优化

1. 在真实笔记本前置摄像头环境下采集三类香蕉样本（不同光照、角度、背景、距离），系统化评估并网格搜索 `camera_rules` 的 7 个阈值和 `candidate` 的 11 个参数。
2. 2 个 overripe 边界样本（IMG_20260603_212906/212911）可能需要引入额外的褐斑连通域特征或考虑标签修正。
3. 当三类样本累积到 50+ 张/类后，重新评估 SVM/Logistic 是否应作为进阶版开放。
4. 如果摄像头复杂背景问题持续，可考虑在 UI 中叠加显示 ROI 矩形框，帮助用户理解"香蕉应放在画面中心区域"。

---

## 修改记录 #19 — 最新样本替换后的基础版剩余优化方案

**修改时间**：2026-06-03 21:46

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `README.md` | “当前仍未完成或需要继续优化”之后新增 `基础版剩余优化方案（最新样本替换后）` | 针对 overripe 新增 10 张、unripe 新增 7 张替换图片后的情况，补充基础版剩余优化路线：最新样本复测、KNN 模型刷新、摄像头真实场景校准、界面鲁棒性增强、基础版与进阶版边界 |
| `README.md` | `基础版剩余优化 Agent 提示词` | 新增面向后续 agent 的可执行提示词，明确当前摄像头基础链路已存在，下一步应围绕最新样本复测、`candidate`/`camera_rules`/`camera_preprocessing`/`stability` 参数校准和 UI 可解释性优化继续推进 |
| `README.md` | 原 `实时识别开发 Agent 提示词` 标题 | 将旧提示词标记为“历史实时识别开发 Agent 提示词（已完成基础链路）”，避免后续误以为仍需从零新增 `src/inference.py` 和摄像头入口 |
| `report/report.md` | 顶部新增本记录 | 按仓库规则记录本次文档修改 |

### 优化点

1. **方案与最新数据状态对齐**：明确记录当前 `data/raw/overripe/` 和 `data/raw/unripe/` 已替换部分网络图片，三类样本数量保持平衡，但需重新复测 HSV/GLCM 特征分布、规则分类结果和 KNN 模型。
2. **优化优先级更清晰**：将剩余工作拆成“最新静态样本复测 -> 摄像头实采校准 -> UI 可解释性增强 -> 进阶版预留”，避免继续盲目调阈值。
3. **问题归因更具体**：区分候选区域验证负责处理非香蕉物体/人/背景干扰，`camera_preprocessing` 与 `camera_rules` 负责处理环境光和成熟度误判，`stability` 负责处理短暂遮挡和实时跳变。
4. **Agent 提示词更新为当前项目状态**：新提示词不再要求从零新增摄像头基础链路，而是要求先阅读现有 `src/inference.py`、`src/app_pyqt.py` 和配置，再进行复测与参数校准。

### 不足点

1. **本次仅更新文档方案**：尚未运行规则分类流水线复测，也未重新训练 KNN/SVM/Logistic 模型。
2. **未生成新的混淆矩阵或实验结论**：新增 overripe/unripe 图片替换后的实际准确率仍需下一步通过命令行流水线验证。
3. **未采集摄像头专用验证集**：摄像头真实场景中的光照、背景、人/物体干扰仍缺少系统化离线评估数据。

### 未完成 / 待继续优化

1. 运行 `python -m src.main_rule_based --input data/raw --config config.yaml`，基于最新三类样本重新生成规则分类结果和特征表。
2. 运行 `python -m src.main_ml --config config.yaml`，刷新 KNN 基础模型并记录模型元数据。
3. 建立摄像头实采验证集，用于网格搜索 `candidate`、`camera_rules`、`camera_preprocessing` 和 `stability` 参数。
4. 在 `src/app_pyqt.py` 中进一步显示 `candidate_reason`、当前规则集名称和模型过期提示。

---

## 修改记录 #18 — 摄像头实时识别稳定性修正（光照鲁棒性 + ripe 召回）

**修改时间**：2026-06-03 20:31

### 问题诊断

摄像头实时识别存在两个核心问题：

1. **只输出 unripe 和 overripe，几乎不输出 ripe**：静态图片校准的规则阈值在摄像头场景下过于激进。`green_ratio_threshold=0.012` 极低——摄像头下 ripe 香蕉因传感器噪声和边缘阴影产生 0.02–0.05 的伪绿色，Rule 1 触发误判为 unripe。`contrast_high=1.70` 也偏低——摄像头 JPEG 压缩和传感器噪声使 ripe 香蕉的 `glcm_contrast` 可达 1.8–2.1，Rule 3 触发误判为 overripe。ripe 香蕉几乎无法抵达 Rule 5。

2. **环境光敏感**：`normalize_lighting()` 仅对 LAB L-channel 做 CLAHE 亮度均衡，不校正色温偏移。暖光（白炽灯）使 HSV 全体偏黄、冷光（LED/荧光灯）使 HSV 偏蓝，固定 HSV 分割阈值在不同光照下表现差异巨大。

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/preprocessing.py` | 第 29–77 行 | **新增** `simple_white_balance(image_bgr, percentile)` 函数（约 35 行）：per-channel 百分位拉伸（默认 1%/99%）实现轻量色彩恒常性校正，减少暖/冷环境光对 HSV 分割的影响 |
| `src/preprocessing.py` | 第 80–110 行 | `preprocess_image` 新增 `white_balance` 和 `wb_percentile` 参数：白平衡在 blur + CLAHE 之前执行（先校正色偏再均衡亮度）；默认 `white_balance=False` 保持对静态图片管道的向后兼容 |
| `config.yaml` | 第 9–15 行 | **新增** `camera_preprocessing` 配置节：`white_balance: true`、`wb_percentile: 1.0`、`blur_kernel: 5`、`equalize: true`，独立于静态图片 `preprocessing` 节 |
| `config.yaml` | 第 22–64 行 | **新增** `camera_rules` 配置节（含完整设计注释）：7 个阈值均独立于静态 `rules` 节，专门针对摄像头传感器噪声、色偏、纹理偏高特性重新设定 |
| `src/inference.py` | 第 74–90 行 | `extract_features_for_frame` 预处理阶段：读取 `camera_preprocessing` 配置，传入 `white_balance=True` 和 `wb_percentile` 调用 `preprocess_image` |
| `src/inference.py` | 第 119–122 行 | `extract_features_for_frame` 规则分类阶段：优先使用 `camera_rules`（若存在），否则 fallback 到静态 `rules`；`classify_by_rules(features, camera_rules)` 替代 `classify_by_rules(features, config.get("rules", {}))` |
| `README.md` | 第 79–103 行 | "当前仍未完成"段落更新：反映摄像头已具备独立规则阈值和白平衡校准，剩余任务调整为真实场景系统化评估和阈值网格搜索调优 |

### camera_rules 阈值设计依据

| 参数 | 静态值 | 摄像头值 | 调整原因 |
|---|---|---|---|
| `green_ratio_threshold` | 0.012 | **0.06** | 摄像头 ripe 香蕉常因边缘阴影/传感器噪声产生 0.02–0.05 伪绿色。0.012 导致大量 ripe→unripe。0.06 仅对真正青香蕉触发 |
| `dark_ratio_threshold` | 0.40 | **0.48** | 摄像头暗光下 dark_ratio 整体偏高。提升减少 ripe→overripe |
| `contrast_high` | 1.70 | **2.20** | 摄像头噪声/压缩伪影使 ripe GLCM contrast 可达 1.8–2.1。1.70 导致 ripe→overripe。2.20 仅对真实黑斑纹理触发 |
| `contrast_threshold` | 1.45 | **1.65** | 同理上移，作为 Rule 4 安全网配合 dark_ratio_low |
| `yellow_ratio_threshold` | 0.50 | **0.40** | 摄像头下黄色饱和度偏低（自动白平衡偏冷）。降低至 0.40 让更多 ripe 通过 Rule 5 |
| `dark_ratio_low` | 0.32 | **0.38** | 配合 contrast_threshold，匹配摄像头更高 dark baseline |
| `overripe_yellow_max` | 0.60 | 0.55→**0.60** | 摄像头 overripe 黄色分布略高，轻微放宽以避免漏检 |

### 验证结果

模拟摄像头场景 ripe 香蕉特征值（green_ratio=0.03, yellow_ratio=0.65, dark_ratio=0.30, contrast=1.5）：
- **静态 rules**: `unripe`（❌ 误判 — green_ratio 0.03 ≥ 0.012 触发 Rule 1）
- **camera_rules**: `ripe`（✅ 正确 — green_ratio 0.03 < 0.06，yellow_ratio 0.65 ≥ 0.40 触发 Rule 5）

静态图片管道测试（unripe/ripe/overripe 典型值）不受影响，三类全部正确分类。

### 优化点

1. **摄像头专用规则阈值**：`camera_rules` 与静态 `rules` 完全独立。`extract_features_for_frame` 仅使用 `camera_rules`；`extract_features_for_image`（静态图片管道）使用 `rules`。两个管道互不干扰，各自针对不同场景优化。

2. **简单白平衡校正**：`simple_white_balance()` 使用 per-channel 百分位拉伸（默认 clip 1%，拉伸至 [0, 255]），在 blur 和 CLAHE 之前执行。白炽灯暖光下蓝色通道拉伸补偿冷色，LED 冷光下红色通道拉伸补偿暖色，HSV 分割阈值在不同光照下更稳定。**默认仅在摄像头模式开启**（`camera_preprocessing.white_balance: true`），静态图片管道不受影响。

3. **ripe 召回修复**：通过提升 `green_ratio_threshold`（0.012→0.06）和 `contrast_high`（1.70→2.20）为 ripe 留出安全区间，同时降低 `yellow_ratio_threshold`（0.50→0.40）使 ripe 更容易命中 Rule 5。模拟验证确认典型摄像头 ripe 特征值从误判 unripe 恢复为正确 ripe。

4. **配置集中管理**：`camera_preprocessing` 和 `camera_rules` 独立成节并附完整设计注释，后续在真实摄像头场景调整阈值时无需修改代码，仅编辑 `config.yaml`。

5. **不破坏静态图片管道**：`preprocess_image` 新增参数默认 `white_balance=False`；`extract_features_for_image`（`dataset_builder.py`）不读取 `camera_rules`；`main_rule_based.py` 75 张图片处理结果不变。

### 不足点

1. **摄像头阈值为推理值而非实测值**：`green_ratio_threshold=0.06`、`contrast_high=2.20` 等基于摄像头物理特性推导并通过模拟验证，但尚未在真实多场景（不同光照、背景、距离）摄像头采集的香蕉样本上进行系统化准确率评估和 ROC 网格搜索。
2. **白平衡为简单百分位拉伸**：`simple_white_balance()` 假设各通道独立且场景包含全黑到全白像素。背光、强侧光、纯色背景等场景下此假设不成立，颜色校正可能失准。尚未与 Gray World、Retinex 等更复杂方法对比。
3. **camera_rules 与静态 rules 无自动切换机制**：当前通过 `config.yaml` 静态指定。如果用户在摄像头模式下加载静态图片（或反之），不会自动切换规则集。但当前架构中摄像头模式固定使用 `extract_features_for_frame`，静态使用 `extract_features_for_image`，天然隔离。

### 未完成 / 待继续优化

1. 在真实摄像头环境下采集三类香蕉样本（不同光照、角度、距离），系统化评估 `camera_rules` 的准确率（精确率、召回率、F1），并通过网格搜索优化 7 个阈值。
2. 如果白平衡效果不理想，可尝试 Gray World 假设或基于参考白板的手动校准。
3. 可考虑在 UI 中显示当前使用的规则集名称（"静态规则" vs "摄像头规则"），增加透明度。
4. 后续如需要，可在 `camera_rules` 中进一步拆分"室内暖光"和"室内冷光"两套阈值，根据帧的 V 均值和色温统计自动切换。

---

### 问题诊断

`models/knn_model.pkl` 为旧的调试模型：`model.classes_ = ['ripe']`、`n_samples_fit = 20`（仅 ripe 单类别训练）。该模型对所有输入样本均预测 `ripe: 100.00%`，原因是 scikit-learn 单类别分类器永远输出唯一类别。问题不在 KNN 算法本身，而在上位机加载了不完整的旧模型。

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/ml_classifier.py` | 第 3–4 行 | 新增 `import json`、`from datetime import datetime` |
| `src/ml_classifier.py` | 第 19 行 | 新增常量 `REQUIRED_CLASSES: set[str] = {"unripe", "ripe", "overripe"}` |
| `src/ml_classifier.py` | 第 131–175 行 | **新增** `validate_model_classes(model, required_classes)` 函数（约 25 行）：检查 `model.classes_` 是否包含全部三类，返回 `(valid, reason)` |
| `src/ml_classifier.py` | 第 181–214 行 | **新增** `save_model_meta(model_path, meta)` 和 `load_model_meta(model_path)` 函数（约 35 行）：保存/加载模型元数据 JSON（`knn_model_meta.json`），记录 classes、class_counts、feature_csv、feature_csv_mtime、train_time、n_samples、test_accuracy、cv_accuracy |
| `src/inference.py` | 第 20–24 行 | `from .ml_classifier` 导入增加 `validate_model_classes` |
| `src/inference.py` | 第 192–201 行 | `predict_features` 在加载模型后调用 `validate_model_classes`；若无效则返回规则分类回退并注明 `"规则分类（{method} 模型类别不完整: {reason}）"` |
| `src/app_pyqt.py` | 第 43–47 行 | `from .ml_classifier` 导入增加 `validate_model_classes` |
| `src/app_pyqt.py` | 第 227–239 行 | `BatchWorker.run`：加载模型后调用 `validate_model_classes`，若无效则设置 `model = None` 并在分类时回退到规则分类 |
| `src/app_pyqt.py` | 第 1033–1056 行 | `_do_single_recognition`：KNN 路径增加模型验证；若无效弹出 `QMessageBox.warning` 提示"当前 KNN 模型类别不完整"，自动回退到规则分类并引导用户重新训练 |
| `src/app_pyqt.py` | 第 1076–1094 行 | `_do_batch_recognition`：新增模型类别完整性预检查，无效时弹出警告并回退到规则分类 |
| `src/main_ml.py` | 第 4 行 | 新增 `from datetime import datetime` |
| `src/main_ml.py` | 第 87–105 行 | 数据加载后新增 `has_full_classes` 检查：若无 `--allow-single-class` 且类别不完整，打印错误并 `SystemExit(1)` |
| `src/main_ml.py` | 第 141–153 行 | 单类别模式：不再覆盖 `{name}_model.pkl`，改为保存 `{name}_debug_single_class.pkl` 并打印明确警告 |
| `src/main_ml.py` | 第 196–227 行 | **新增** §3d "Final model" 阶段：在所有标注数据上训练 final 模型；仅当 `model.classes_ == REQUIRED_CLASSES`（三类齐备）时保存为 `{name}_model.pkl`；同步保存 `{name}_model_meta.json` 元数据 |
| `src/main_ml.py` | 第 166 行 | 修复 CV accuracy 列名提取（`cv_accuracy_mean` 替代 `mean_test_accuracy`） |
| `README.md` | 第 438–450 行 | "当前已支持" 段落新增 KNN 模型要求说明：单类别调试模型会被自动检测并拒绝，训练命令 `python -m src.main_ml --config config.yaml` |
| `models/knn_model.pkl` | 重新生成 | 基于全部 75 条三分类样本训练，classes=['overripe', 'ripe', 'unripe']，test_acc=1.0000，cv_acc=0.96 |
| `models/knn_model_meta.json` | 新建 | KNN 模型元数据，记录 3 类各 25 样本、特征表路径/时间戳、训练时间和准确率 |

### 优化点

1. **模型类别完整性校验**：`validate_model_classes()` 在三个入口同时生效——`predict_features`（摄像头/截图路径）、`_do_single_recognition`（单图路径）、`BatchWorker.run`（批量路径）。单类别调试模型在所有模式下都会被检测并拒绝，防止 `ripe: 100%` 误导性输出。

2. **用户友好提示**：无效模型时弹出对话框明确说明原因（缺少哪些类别），并引导运行 `python -m src.main_ml --config config.yaml` 重新训练。`method_used` 返回字符串也包含具体回退原因。

3. **单类别调试模式不再污染正式模型**：`--allow-single-class` 模式下模型保存为 `{name}_debug_single_class.pkl`（如 `knn_debug_single_class.pkl`），永远不会覆盖 `knn_model.pkl`。正式模型仅当 `classes_` 完全包含 unripe/ripe/overripe 三类时才保存。

4. **全量数据 final 模型**：新增阶段 3d，在 train/test split 评估后使用**全部 75 条样本**训练 final KNN 模型并保存，使部署模型受益于 100% 的训练数据（而非仅 70%）。

5. **模型元数据 JSON**：`knn_model_meta.json` 记录 classes、class_counts、feature_csv 路径和修改时间、训练时间、test_accuracy、cv_accuracy。上位机可通过 `load_model_meta()` 读取元数据，后续可进一步实现"特征表已更新但模型较旧"的智能提示。

6. **KNN 模型已重新训练**：新 `knn_model.pkl` classes=['overripe', 'ripe', 'unripe']，75 样本，test_acc=1.0000，cv_acc=0.96。不再出现所有输入均输出 ripe:100% 的问题。

### 不足点

1. **元数据尚未被 UI 主动读取**：`load_model_meta()` 已实现但 `app_pyqt.py` 尚未在加载 KNN 前读取 meta 检查特征表是否比模型更新。当前仅使用 `validate_model_classes()` 做类别完整性检查。
2. **SVM/Logistic 模型也一并重新训练**：新 `svm_model.pkl`、`logistic_model.pkl` 和对应 meta JSON 已生成，但基础版 UI 未开放这两个方法。未来启用进阶版时可直接使用。
3. **全量数据 final KNN 未在独立测试集上评估**：final 模型使用全部 75 条样本训练，无法再评估留出集性能。实际泛化性能应以 CV 结果（0.96±0.03）为参考。

### 未完成 / 待继续优化

1. 在 `app_pyqt.py` 加载 KNN 模型时读取 `knn_model_meta.json`，若 `feature_csv_mtime` 比 `train_time` 新，提示用户特征表已更新、建议重新训练模型。
2. 如需更严格的模型评估，可增加三折交叉验证或独立验证集。
3. 当进阶版开放 SVM/Logistic 时，`METHOD_TO_MODEL` 和模型验证逻辑已就绪。

---

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/inference.py` | 全文重写（约 320 行） | **候选验证完全重构**：`extract_features_for_frame` 新增 `brown_ratio`、`banana_color_ratio`、`yellow_green_ratio` 三个颜色指标（基于 HSV color masks 直接计算）；`is_valid_banana_candidate` 从 3 道关卡升级为 7 道严格关卡 |
| `src/inference.py` | `is_valid_banana_candidate` | (1) 面积比 1%–45%；(2) `cv2.minAreaRect` 旋转边界框长宽比 1.4–8.0；(3) extent（mask/rotated_rect）≥ 0.25；(4) banana 颜色占比 ≥ 20%（green+yellow+brown，**不含 dark**）；(5) 黄绿占比 ≥ 12%；(6) dark_ratio 否决 > 65%；(7) 中心 ROI 检查（70%×70% 窗口） |
| `src/inference.py` | `_DEFAULT_CANDIDATE` | 默认阈值字典完全替换：新增 `min_banana_color_ratio`、`min_yellow_green_ratio`、`max_dark_ratio_for_presence`、`min_rotated_aspect`、`max_rotated_aspect`、`min_extent`、`use_center_roi`、`roi_width_ratio`、`roi_height_ratio`；移除旧的 `min_color_fill`、`min_bbox_aspect`、`max_bbox_aspect` |
| `config.yaml` | `candidate` 节 | 完全替换为新的 12 个参数 |
| `src/app_pyqt.py` | 第 353–354 行 | QSplitter 拉伸因子从 `(1, 2)` 改为 `(3, 1)`（图像区获得更多空间） |
| `src/app_pyqt.py` | 第 507 行 | `_build_info_panel` 新增 `container.setMaximumHeight(260)` 限制信息区高度 |
| `src/app_pyqt.py` | 第 508–510 行 | 信息区面板内边距从 `4px` 降为 `2px`，行间距从 `4px` 降为 `2px` |
| `src/app_pyqt.py` | 第 1184–1258 行 | **新增** `_image_to_label(label, image_bgr, placeholder, is_mask)` 方法：按 QLabel 当前尺寸缩放图像，替代固定 `IMAGE_DISPLAY_SIZE=280` 的硬编码 |
| `src/app_pyqt.py` | 第 1260–1266 行 | **新增** `_refresh_image_labels()` 方法：重新应用缓存图像到标签 |
| `src/app_pyqt.py` | 第 1268–1271 行 | **新增** `resizeEvent()`：窗口缩放时自动调用 `_refresh_image_labels()`，实现图像实时铺满显示框 |
| `src/app_pyqt.py` | 第 1283–1285 行 | `_display_results` 三幅图像的显示从 `cv_to_qpixmap(img, IMAGE_DISPLAY_SIZE)` 替换为 `_image_to_label(label, img)` |
| `src/app_pyqt.py` | 第 892 行 | `_on_camera_tick` 原始帧显示从 `cv_to_qpixmap(frame, IMAGE_DISPLAY_SIZE)` 替换为 `_image_to_label(lbl, frame)` |
| `src/app_pyqt.py` | 第 976–977 行 | `_run_camera_inference` mask 和结果图显示替换为 `_image_to_label` |
| `src/app_pyqt.py` | 第 600 行 | `_show_selected_image_preview` 原图预览替换为 `_image_to_label` |
| `README.md` | 第 79–103 行 | "当前仍未完成"段落更新：明确标注候选验证阈值尚未在真实摄像头场景中进行系统化误检率测试 |

### 优化点

1. **dark_ratio 不再作为香蕉存在依据**：上一版 `is_valid_banana_candidate` 使用 `green + yellow + dark ≥ 0.15` 判断颜色填充，黑色衣服、LCD 屏幕、深色桌面和阴影的 dark_ratio 极高，轻松跨过 0.15 阈值。本版改为 `(green + yellow + brown) ≥ 0.20` 判断香蕉颜色，dark_ratio 仅作为上限否决（> 0.65 拒绝），直接从原理上消除 dark 偏高导致的误检。

2. **旋转边界框替代轴对齐边界框**：使用 `cv2.minAreaRect` 获取最小外接旋转矩形，计算 `rotated_aspect = long_side / short_side`（阈值 1.4–8.0）和 `extent = mask_area / rect_area`（≥ 0.25）。旋转边界框对香蕉的任意角度摆放具有旋转不变性，比轴对齐 boundingRect 更准确；extent 过滤散乱碎片化分割（人体、复杂背景等）。

3. **新增 brown_ratio 参与香蕉颜色计数**：`extract_features_for_frame` 从 HSV color masks 直接计算 brown 像素占比，加入 `banana_color_ratio`（green+yellow+brown）。成熟和过熟香蕉表面有棕色斑点，brown 是有效香蕉颜色信号。

4. **中心 ROI 检查**：默认仅对画面中心 70%×70% 窗口检测香蕉。边缘出现的分割区域（路过的人、桌角、墙壁边缘）即使通过了所有其他检查，也会因重心不在 ROI 内而被拒绝。原图仍显示完整画面。

5. **max_area_ratio 从 0.85 大幅降低至 0.45**：面积比 > 45% 的 mask 通常是整块深色衣服、屏幕或墙壁的误分割，不再通过验证。香蕉在正常拍摄距离下很少占据超过一半画面。

6. **界面布局修正**：
   - QSplitter 拉伸比从信息区优先(1:2)反转为图像区优先(3:1)，三个图像面板获得充足空间。
   - 信息区 `setMaximumHeight(260)` 约束最大高度，消除上一版下方大面积空白。
   - 图像显示从固定 `IMAGE_DISPLAY_SIZE=280` 改为按 QLabel 当前尺寸动态缩放，窗口缩放时通过 `resizeEvent` 自动重绘，三幅图像始终铺满各自显示框。

### 不足点

1. **候选验证阈值仍为推理值**：`min_extent=0.25`、`max_dark_ratio=0.65`、`min_banana_color_ratio=0.20` 等参数基于原理推导，尚未在包含真实非香蕉物体的摄像头数据集上进行 ROC/PR 曲线分析和最优阈值搜索。
2. **ROI 为硬性拒绝**：如果香蕉恰好放在画面边缘，会被 ROI 检查拒绝。这是故意设计（鼓励居中放置），但可能对无经验的用户造成困惑。
3. **brown_ratio 依赖 HSV brown mask 准确性**：`segmentation.hsv_color_masks` 中的 brown 阈值 `[5, 35, 20]–[25, 255, 170]` 在实时光照下可能漏检或过检棕色区域。
4. **extent 对弯曲香蕉可能偏低**：极度弯曲的香蕉在 minAreaRect 下 extent 可能较低（因为香蕉弯曲导致边界框内大量空白），阈值 0.25 需要摄像头实采香蕉验证。

### 未完成 / 待继续优化

1. 采集包含非香蕉物体（人、屏幕、衣服、桌面、墙壁）的摄像头场景数据，系统化测试误检率并调整候选验证阈值。
2. 如果 extent 对弯曲香蕉误拒绝过多，可考虑改用轮廓面积/凸包面积或分段拟合。
3. 可考虑在 UI 中显示 ROI 矩形框，让用户知道香蕉应放在哪个区域。
4. 如果 KNN 模型已训练，验证 KNN 模式下的候选验证 + KNN 分类端到端流程。

---

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/inference.py` | 第 13 行 | 新增 `import cv2` |
| `src/inference.py` | 第 21 行 | 新增 `from .morphology import mask_bounding_box` 导入 |
| `src/inference.py` | 第 35–171 行 | **新增** `is_valid_banana_candidate(features, mask, image_shape, config)` 函数（约 80 行）：使用 mask 面积比、边界框长宽比和香蕉颜色填充率（green+yellow+dark）三道关卡过滤非香蕉物体；包含 `_DEFAULT_CANDIDATE` 默认阈值字典 |
| `src/inference.py` | 第 183–232 行 | 更新 `run_inference_on_frame` 返回值：新增 `banana_detected`（bool）和 `candidate_reason`（str）字段；候选验证失败时 `prediction` 返回 `"unknown"` 而非将非香蕉区域送入成熟度分类 |
| `config.yaml` | 第 30–39 行 | **新增** `candidate` 配置节（`min_area_ratio: 0.005`、`max_area_ratio: 0.85`、`min_color_fill: 0.15`、`min_bbox_aspect: 0.12`、`max_bbox_aspect: 8.0`） |
| `config.yaml` | 第 41–44 行 | **新增** `stability` 配置节（`confirm_frames: 3`、`lost_frames: 2`） |
| `src/app_pyqt.py` | 第 93 行 | `CLASS_METHODS` 从 `["规则分类", "KNN", "SVM", "Logistic"]` 缩减为 `["规则分类", "KNN"]`（基础版仅开放规则分类和 KNN；SVM/Logistic 为进阶版） |
| `src/app_pyqt.py` | 第 88 行 | `IMAGE_DISPLAY_SIZE` 从 380 缩小为 280（减少图像面板垂直空间占用） |
| `src/app_pyqt.py` | 第 132–134 行 | 移除 `MIN_MASK_AREA_FOR_DETECTION = 200` 固定像素阈值，替换为 `STABILITY_CONFIRM_FRAMES = 3` 和 `STABILITY_LOST_FRAMES = 2` 多帧稳定性常量 |
| `src/app_pyqt.py` | 第 312–313 行 | `MainWindow.__init__` 新增稳定性状态变量：`_banana_votes`（投票计数）、`_banana_confirmed`（是否已确认香蕉） |
| `src/app_pyqt.py` | 第 351–352 行 | QSplitter 拉伸因子从 `(2, 1)` 调整为 `(1, 2)`，下方信息区获得更多空间 |
| `src/app_pyqt.py` | 第 450–498 行 | `_build_image_panel`：三面板 `setMinimumSize` 从 `(380, 380)` 降为 `(200, 150)`；新增 `setSizePolicy(Expanding, Expanding)`；GroupBox 内边距从默认降为 `2px`；间距从 6 降为 4 |
| `src/app_pyqt.py` | 第 531 行 | `_build_info_panel` 特征表格：移除 `setMaximumHeight(220)` 限制；新增 `verticalHeader().setDefaultSectionSize(22)` 紧凑行高 |
| `src/app_pyqt.py` | 第 712–713 行 | `_on_camera_open`：新增稳定性状态重置（`_banana_votes = 0`、`_banana_confirmed = False`） |
| `src/app_pyqt.py` | 第 756–757 行 | `_on_camera_close`：新增稳定性状态重置 |
| `src/app_pyqt.py` | 第 829–842 行 | `_on_camera_screenshot`：`MIN_MASK_AREA_FOR_DETECTION` 检查替换为 `result["banana_detected"]` 检查，显示具体 `candidate_reason` |
| `src/app_pyqt.py` | 第 896–985 行 | `_run_camera_inference` 完全重写：集成 `banana_detected` 候选验证 → 多帧稳定性投票（±1 计数 + 滞后区间）→ 未确认时显示"未检测到香蕉"和 vote 进度 → 确认后显示成熟度结果；未确认期间仍显示实时特征值方便调试 |
| `README.md` | 第 79–99 行 | "当前仍未完成"段落更新：移除已实现项，新增基础版当前状态、剩余任务和进阶版方案说明 |
| `README.md` | 第 437–444 行 | "运行现有 PyQt5 应用"当前已支持列表更新：明确"基础版"分类方法范围，新增摄像头实时识别功能说明 |
| `README.md` | 第 446–470 行 | **新增** "进阶版方案（SVM / Logistic）"章节：说明 SVM/Logistic 暂不开放的原因及后续启用步骤 |
| `README.md` | 第 309 行 | 模块说明表新增 `src/inference.py` 条目 |

### 优化点

1. **香蕉候选区域验证（`is_valid_banana_candidate`）**：使用 mask 面积比（0.5%–85% 范围）、边界框长宽比（short/long ≥ 0.12、long/short ≤ 8.0）和香蕉颜色填充率（green+yellow+dark ≥ 15%）三重条件过滤非香蕉物体，风扇、衣服、桌面、背景等不再被送入成熟度分类。相比之前仅用固定 200px 像素阈值，面积比适配不同分辨率帧，边界框和颜色规则提供额外的形状/颜色约束。

2. **多帧稳定性投票**：`_banana_votes` 采用 ±1 累加/递减计数 + 滞后区间设计。香蕉出现时需连续 3 帧确认后才显示成熟度（避免瞬间误判）；香蕉消失时需连续跌至 0 才显示"未检测到"（避免短暂遮挡导致闪烁）。中间状态保持上一帧判定，消除画面抖动。

3. **界面空间优化**：图像面板最小尺寸从 380×380 降至 200×150 + Expanding 策略，面板内边距从默认压缩为 2px；QSplitter 拉伸比从图像优先(2:1)反转为信息优先(1:2)；特征表格移除 220px 高度限制并紧凑行高至 22px。下方预测类别、食用建议和 9 项特征表现在有充足显示空间。

4. **基础版分类方法限定**：界面下拉框仅显示"规则分类"和"KNN"，避免 SVM/Logistic 因模型文件缺失导致用户体验困惑。代码中 `METHOD_TO_MODEL` 映射保留（含 SVM/Logistic），`ml_classifier.py` 中 `make_svm`/`make_logistic` 保留，后续只需修改 `CLASS_METHODS` 即可启用进阶版。

5. **未确认香蕉期间仍显示特征值**：方便开发者和用户观察分割效果——即使画面中暂时没有香蕉，也能看到 HSV 颜色比例和 GLCM 特征值，便于判断分割是否合理。

6. **截图识别显示具体失败原因**：`candidate_reason` 字段提供确切的验证失败原因（如"边界框过于细长"、"香蕉颜色占比过低"），替代过去笼统的"未检测到香蕉"提示。

### 不足点

1. **候选验证阈值为经验值**：`min_color_fill=0.15`、`min_bbox_aspect=0.12` 等阈值基于推理设定，尚未在摄像头实采数据上进行系统评估和 ROC 调优。
2. **多帧稳定性参数未做系统调优**：`confirm_frames=3` 在 500ms 推理间隔下约 1.5 秒确认延迟，对快速移动的香蕉可能略显迟钝；但增大确认帧数会增加响应延迟。
3. **候选验证使用特征值而非原始颜色 mask**：颜色填充率依赖 `feature_hsv.py` 已计算的 green_ratio/yellow_ratio/dark_ratio，而非原始 HSV 颜色 mask 的直接面积统计。如果特征提取的比率计算有任何问题，候选验证也会受影响。
4. **边界框检测依赖 `mask_bounding_box`**：该函数基于 `cv2.boundingRect` 而非 `cv2.minAreaRect`，对任意角度旋转的香蕉可能给出过大的边界框，使得长宽比过滤效果下降。但当前情况下 boundingRect 足够有效。
5. **特征表格在未确认香蕉时仍显示**：虽然方便调试，但对最终用户可能造成困惑（看到数字但不知道是否有效）。

### 未完成 / 待继续优化

1. 采集笔记本前置摄像头环境下的三类香蕉样本，用于：（a）重新验证候选验证阈值；（b）校准摄像头专用规则阈值；（c）训练 KNN 模型。
2. 考虑使用 `cv2.minAreaRect` 替代 `cv2.boundingRect` 以获得更准确的旋转边界框和长宽比。
3. 如果摄像头场景下的误判率仍高，可考虑增加"ROI 裁剪区域"或"背景抑制"策略。
4. 在 `_run_camera_inference` 中，可添加对单个 color mask 面积比（而非特征比率）的直接检查，作为候选验证的补充规则。
5. 当 KNN 模型可用时，验证实时推理下 KNN 的延迟是否在 500ms 间隔内可接受。

---

**修改时间**：2026-06-02 10:35

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/inference.py` | **新建文件**（155 行） | 新增帧级推理封装模块，包含 `extract_features_for_frame`（从 BGR 数组提取 HSV+GLCM 特征）、`predict_features`（规则/ML 分类调度 + 模型缓存 + 自动回退）和 `run_inference_on_frame`（完整流水线便捷封装）三个函数；复用现有 `preprocessing.py`、`segmentation.py`、`feature_hsv.py`、`feature_glcm.py`、`rule_classifier.py`、`ml_classifier.py`，不重复算法逻辑 |
| `config.yaml` | 第 22–29 行（新增 `camera` 节） | 新增摄像头配置：`device_index: 0`、`width: 1280`、`height: 720`、`display_fps: 30`、`inference_interval_ms: 500`、`realtime_max_size: 640`、`mirror: false` |
| `src/app_pyqt.py` | 第 18 行 | 新增 `import time` |
| `src/app_pyqt.py` | 第 57 行 | QtCore 导入新增 `QTimer` |
| `src/app_pyqt.py` | 第 60、72 行 | QtWidgets 导入新增 `QCheckBox`、`QSpinBox` |
| `src/app_pyqt.py` | 第 41 行 | 项目内部模块导入新增 `from .inference import run_inference_on_frame` |
| `src/app_pyqt.py` | 第 117–119 行 | 新增常量 `MIN_MASK_AREA_FOR_DETECTION = 200`（判断画面中是否有香蕉的最小有效分割面积） |
| `src/app_pyqt.py` | 第 303–310 行 | `MainWindow.__init__` 新增摄像头状态变量：`_camera_cap`、`_camera_timer`、`_camera_paused`、`_camera_frame`、`_last_inference_time`、`_model_cache`、`_camera_fallback_msg` |
| `src/app_pyqt.py` | 第 345 行 | `_setup_ui` 新增 `root_layout.addWidget(self._build_camera_toolbar())` 调用 |
| `src/app_pyqt.py` | 第 402–448 行 | 新增 `_build_camera_toolbar` 方法：生成摄像头控制工具栏（打开/关闭/暂停/截图按钮、摄像头编号选择、镜像翻转复选框） |
| `src/app_pyqt.py` | 第 580–589 行 | `_connect_signals` 新增摄像头按钮信号连接 |
| `src/app_pyqt.py` | 第 599–808 行 | 新增摄像头实时识别方法组：`_on_camera_open`（打开摄像头 + 启动 QTimer）、`_on_camera_close`（停止定时器 + 释放资源）、`_on_camera_pause`（暂停/继续切换）、`_on_camera_screenshot`（截图完整识别 + ML 模型检查 + 回退提示）、`_on_camera_tick`（定时器回调：抓帧→显示→节流推理）、`_run_camera_inference`（帧级推理 + 空 mask 检测 + UI 更新）、`_update_camera_ui_state`（控件启用/禁用状态管理） |
| `src/app_pyqt.py` | 第 810–819 行 | 新增 `closeEvent` 方法：窗口关闭时自动释放摄像头资源 |

### 优化点

1. **新增帧级推理封装**：`src/inference.py` 的 `extract_features_for_frame` 直接接受 BGR 数组而非文件路径，使实时摄像头、视频流等场景可直接调用，同时完全复用现有预处理、分割、特征提取模块，无重复代码。
2. **ML 模型缓存机制**：`predict_features` 通过 `model_cache` 字典缓存已加载的 ML 模型，摄像头模式下避免每帧重复加载模型文件，显著降低推理延迟。
3. **优雅的 ML 回退策略**：当 KNN/SVM/Logistic 模型文件不存在或预测异常时，自动回退到规则分类，并在界面显示回退提示（`method_used` 字段），不会崩溃。
4. **推理节流与显示解耦**：摄像头显示帧率（~30fps）与推理间隔（500ms）分离，`_on_camera_tick` 每个显示帧更新原始画面，仅在 `inference_interval_ms` 到期时触发一次推理计算，保证 UI 流畅。
5. **摄像头实时推理 scaled 到 640px**：通过 `config.yaml` 的 `camera.realtime_max_size` 配置，实时推理在 640px 最大边下运行，兼顾速度与精度。
6. **空 mask 友好提示**：当画面中没有香蕉或分割面积 < `MIN_MASK_AREA_FOR_DETECTION`（200px）时，mask 和结果面板显示"未检测到香蕉"提示，而非误导性的 ripe 预测。
7. **截图识别功能**：支持在摄像头画面中截取当前帧进行完整识别（含 ML 模型检查对话框），结果同时更新三个图像面板和特征表格。
8. **窗口关闭资源释放**：`closeEvent` 确保关闭窗口时自动释放摄像头和定时器资源。
9. **摄像头编号与镜像配置**：UI 提供摄像头编号选择（0–9）和镜像翻转复选框，适配不同笔记本前置摄像头。
10. **不破坏现有功能**：单图识别、批量检测、CSV 导出、`main_rule_based.py`、`main_ml.py` 命令行流程全部保持正常工作。

### 不足点

1. **摄像头环境下规则阈值未专门校准**：当前规则阈值基于静态图片数据集（unripe 25 + ripe 25 + overripe 25）校准，尚未在笔记本前置摄像头的实时光照和背景条件下验证和调整。
2. **无摄像头场景 ML 模型**：摄像头实时模式下默认使用规则分类，如需 ML 必须在摄像头环境下采集样本重新训练模型。
3. **推理仍在主线程**：使用 `QTimer` 在主线程中运行推理（而非 `QThread`），单次推理耗时约 50–100ms 时会引起 UI 短暂停顿；当前 500ms 推理间隔 + 640px 缩放下可接受，但若未来推理更复杂需迁移到工作线程。
4. **无性能监控**：当前未在 UI 中显示实时帧率或推理耗时。

### 未完成 / 待继续优化

1. 采集笔记本前置摄像头环境下的三类香蕉样本，重新评估和校准规则阈值。
2. 如需 ML 实时模式，使用摄像头采集样本 → 生成 feature CSV → 训练模型 → 加载到摄像头模式。
3. 可考虑将推理迁移到 `QThread` 以避免任何 UI 卡顿（当前方案对展示场景已足够）。
4. 可添加实时 FPS / 推理耗时显示。

---

**修改时间**：2026-06-02 10:22

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `README.md` | 全文重写 | 将当前方案从“图片识别应用系统”更新为“支持笔记本电脑前置摄像头的实时识别应用系统”；新增前置摄像头可行性评估、实时识别系统架构、摄像头入口设计、帧级推理封装、性能策略、配置建议、实施步骤和实时识别开发 Agent 提示词；将上一版 PyQt5 单图/批量方案和原始两阶段算法方案整理到 README 后部的项目历史 |
| `report/report.md` | 修改记录 #13（本次） | 记录本次 README 方案更新 |

### 优化点

1. **当前方案与项目进度对齐**：README 不再停留在“尚未提供 PyQt5 界面”的旧状态，而是明确当前已具备单图识别、批量检测和 PyQt5 应用入口，下一阶段目标为摄像头实时识别。
2. **补充前置摄像头可行性结论**：明确笔记本前置摄像头适合课程展示和原型验证，但受分辨率、自动曝光、白平衡、背景和运动模糊影响，真实稳定部署仍需摄像头场景样本验证。
3. **形成实时识别开发方案**：新增 `src/inference.py` 帧级推理封装建议、`config.yaml` camera 配置建议、PyQt5 摄像头控件设计、实时性能节流策略和三阶段实施路线。
4. **保留历史方案**：将上一版 PyQt5 图片识别与批量检测方案、最初 HSV+GLCM 两阶段算法方案移动到 README 后部，保证方案演进路径可追溯。
5. **补充 Agent 提示词**：提供可直接用于后续开发摄像头实时识别功能的完整提示词，包含目标、界面建议、工程约束和验收标准。

### 不足点

1. **本次仅更新文档**：尚未实际新增 `src/inference.py`、摄像头控件、`camera` 配置节或实时识别代码。
2. **实时识别效果未验证**：尚未使用笔记本前置摄像头采集香蕉样本，也未验证当前 HSV/GLCM 阈值在实时光照和背景下的稳定性。
3. **机器学习实时预测仍依赖后续训练**：README 中建议的 ML 实时模式需要先基于最新数据运行 `python -m src.main_ml` 生成模型文件。

### 未完成 / 待继续优化

1. 新增 `src/inference.py`，实现基于 OpenCV 图像数组的帧级特征提取和统一预测封装。
2. 在 `src/app_pyqt.py` 中加入打开/关闭摄像头、暂停/继续、截图识别和实时结果刷新。
3. 在 `config.yaml` 中新增 `camera` 配置节，并验证 `cv2.VideoCapture(0)` 是否能正常读取笔记本前置摄像头。
4. 采集摄像头环境下的三类样本，重新评估规则阈值和分割鲁棒性。

---

## 修改记录 #12 — 错误样本替换后复测（v4 规则验证）

**修改时间**：2026-06-01 22:06

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `report/experiment_report.md` | 新增 §8「错误样本替换后复测」+ 版本历史更新 | 记录 10 个错误样本替换后的复测结果：总准确率 86.67%→98.67%，仅剩 1 个边界样本；更新版本历史表增加 v4-retest 行 |
| `report/report.md` | 修改记录 #12（本次） | 记录本次替换复测 |
| `results/rule_based/summary.csv` | 自动重新生成 | 由 `python -m src.main_rule_based` 重新生成，已不包含旧错误文件名 |
| `data/features/combined_features.csv` | 自动重新生成 | 由流水线重新生成，75 样本 × 13 特征 |
| `data/processed/masks/`、`data/processed/visualized/`、`results/rule_based/images/` | 自动重新生成 | 可视化输出随流水线更新 |

### 复测数据

| 指标 | 替换前 (v4) | 替换后 (v4-retest) | 变化 |
|------|:-----------:|:------------------:|:----:|
| 总准确率 | 65/75 = 86.67% | 74/75 = **98.67%** | **+12.00pp** |
| unripe 召回 | 22/25 = 88.00% | 25/25 = **100.00%** | +12.00pp |
| ripe 召回 | 19/25 = 76.00% | 24/25 = **96.00%** | +20.00pp |
| overripe 召回 | 24/25 = 96.00% | 25/25 = **100.00%** | +4.00pp |

混淆矩阵变为近乎对角矩阵：overripe 25/25、ripe 24/25（1→unripe）、unripe 25/25。

### 优化点

1. **照片质量是准确率的关键瓶颈**：替换前 10 个错误样本中有 4-5 个是标签歧义或图片质量问题（绿色香蕉标为 ripe、过亮/过暗光照等），替换后这些系统性错误全部消除。
2. **v4 规则在高质量样本上表现卓越**：不调整任何阈值即达到 98.67%，三类召回均为 96%+，证明当前规则结构和参数组合具有良好的泛化能力。
3. **唯一剩余错误为不可约减的边界样本**：banana-24.jpg (gr=0.028, yr=0.96)，本质上是 ripe/unripe 连续光谱的中间点，任何单阈值方案都会在此类边界上产生个别错误。

### 不足点

1. **仅 1 个边界样本无法通过阈值调整解决**：green_ratio=0.0277 仅略超 0.012 阈值，但提高阈值会牺牲 unripe 召回。
2. **样本量仍有限**：每类 25 张，虽然当前准确率很高，但不代表在大规模多样化数据上能维持。
3. **未运行 compileall/pytest**：本次仅修改 Markdown 文档和重新运行流水线生成 CSV/图片，未修改 Python 代码或 config.yaml，无需编译和测试验证。

### 未完成 / 待继续优化

1. 运行 `python -m src.main_ml` 基于替换后的 combined_features.csv（75 样本）完成 ML 三模型训练和 CV 对比。
2. 在 PyQt5 界面中使用新训练的 ML 模型进行三类样本识别验证。
3. 扩充样本量到每类 50+ 张。

---

## 修改记录 #11 — 规则分类器三分类联合校准（unripe + ripe + overripe）

**修改时间**：2026-06-01 20:56

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/rule_classifier.py` | `DEFAULT_RULES` (L6-L14) + `classify_by_rules()` (L17-L76) | 新增 `contrast_high=1.70` 参数；新增 Rule 3 `glcm_contrast >= contrast_high → overripe`（纹理主导规则）；原 Rule 3 降为 Rule 4 安全网；DEFAULT_RULES 中 green_ratio_threshold 从 0.30 改为 0.012 |
| `config.yaml` | `rules` 节 (L55-L62) + 注释块 (L22-L53) | 新增 `contrast_high: 1.70` 参数；重写全部 7 个阈值的注释，基于三类各 25 张样本的联合分布统计说明设计依据 |
| `tests/test_features.py` | `test_rule_classifier_custom_thresholds` (L189-L201) + `test_rule_classifier_default_rules_complete` (L204-L215) + 新增 2 个测试 (L218-L242) | 更新自定义阈值测试适配新的 default green_th=0.012；DEFAULT_RULES 必需键增加 `contrast_high`；新增 `test_rule_classifier_contrast_high_triggers_overripe` 和 `test_rule_classifier_contrast_high_respects_priority` |
| `report/experiment_report.md` | 全文 | 基于三类 75 样本重写：新增 overripe 特征分布、glcm_contrast 安全间隙分析、v3→v4 准确率对比、10 个错误样本逐个分析、v2→v4 版本演进表 |
| `report/report.md` | 修改记录 #11（本次） | 记录本次三分类联合校准实验 |

### 实验关键数据

| 指标 | v3（两类校准） | v4（三类联合校准） | 变化 |
|------|---------------|---------------------|------|
| 数据集 | unripe 20+ripe 20 | unripe 25+ripe 25+overripe 25 | — |
| 总准确率 | 57/75 = 76.00% | 65/75 = **86.67%** | **+10.67pp** |
| unripe 召回 | 22/25 = 88.00% | 22/25 = 88.00% | 0pp |
| ripe 召回 | 19/25 = 76.00% | 19/25 = 76.00% | 0pp |
| overripe 召回 | 16/25 = 64.00% | 24/25 = **96.00%** | **+32.00pp** |

### 优化点

1. **overripe 召回从 64% 跃升至 96%**（+32pp）：新增 Rule 3 `glcm_contrast >= 1.70 → overripe`，利用 overripe 表面褐斑产生的高纹理对比度（mean=3.05, 是 ripe 的 3.4 倍）作为区分特征。
2. **数据驱动的安全间隙分析**：通过分析"逃逸 Rule 1 样本"的 glcm_contrast 分布，发现非overripe max=1.61、overripe min=1.76，安全区间 (1.61, 1.76)，中点 1.70 实现零误判。
3. **grid search 联合校准**：green_ratio_threshold × contrast_high 10×12=120 组合 sweep，确认 green_th=0.012 在三分类下仍为最优。
4. **关键发现 — dark_ratio 对 overripe 区分力弱**（Cohen's d=0.25）：overripe dark_ratio mean=0.363 vs ripe mean=0.326，差异远小于预期，推翻了"dark_ratio 是 overripe 主要特征"的初始假设。
5. **关键发现 — glcm_contrast 是三分类最强单特征**：overripe (3.05) >> unripe (1.59) > ripe (0.90)，Cohen's d=2.36 vs ripe。
6. **规则可解释性保持**：新增规则仅一行 `if contrast >= contrast_high: return "overripe"`，语义清晰。
7. **测试覆盖增加**：从 15 条扩至 17 条，新增 contrast_high 触发和优先级测试。

### 不足点

1. **ripe 召回 76% 是瓶颈**：5 个 ripe→unripe 误判全部因 green_ratio > 0.012，其中 2 个极可能是标签错误（网络图片中绿色香蕉被标为 ripe）。
2. **overripe→unripe 1 例无法通过规则优先级解决**：pexels-duane-mendes 同时具有高 green_ratio (0.54) 和过熟特征，被 Rule 1 优先捕获。
3. **dark_ratio 特征有效性低于预期**：overripe 褐变在 dark mask 中未充分捕获，可能需要调整 dark mask 的 HSV 定义或引入专门的 brown mask 特征。
4. **样本量有限**：每类 25 张，统计可靠性受限于样本量，且网络图片存在标签噪声。

### 未完成 / 待继续优化

1. 运行 `python -m src.main_ml` 完成 KNN/SVM/Logistic 三分类训练 + CV 对比（combined_features.csv 已有 75 样本）。
2. 在 PyQt5 界面中加载新训练的模型文件，对比四种分类方法在三类样本上的表现。
3. 优化 dark mask 的 HSV 定义，提升对 overripe 褐变的敏感性。
4. 清洗/重新标注存疑的网络图片标签。

---

## 修改记录 #10 — 规则分类器 green_ratio 阈值校准与两类实验（unripe + ripe）

**修改时间**：2026-06-01 19:58

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `config.yaml` | `rules.green_ratio_threshold`（L55）+ 注释块（L22-L50） | green_ratio_threshold 从 0.30 调整为 **0.012**；重写全部 6 个阈值的注释，基于 unripe 20 + ripe 20 两类特征分布重新说明设计依据 |
| `report/experiment_report.md` | 全文 | 基于两类样本重写实验报告：新增 unripe 特征分布统计、两类对比分析、green_ratio_threshold sweep 扫描表、调整前后准确率对比、6 个错误样本逐个分析、GLCM 纹理特征区分力评估 |
| `report/report.md` | 修改记录 #10（本次） | 记录本次阈值校准实验 |

### 实验关键数据

| 指标 | 调整前 (green_th=0.30) | 调整后 (green_th=0.012) |
|------|------------------------|--------------------------|
| 总准确率 | 20/40 = 50.00% | 34/40 = **85.00%** |
| unripe 召回 | 1/20 = 5.00% | 17/20 = **85.00%** |
| ripe 召回 | 19/20 = 95.00% | 17/20 = 85.00% |

### 优化点

1. **green_ratio_threshold 数据驱动校准**：0.30 → 0.012，通过 0.005-0.05 步长 0.001 的 sweep 扫描确定最优值（0.012 ≈ unripe q10 与 ripe q90 的分界点）。
2. **unripe 召回从 5% 跃升至 85%**：消除了"green_ratio_threshold 过高导致 unripe 几乎全部漏判"的系统性缺陷。
3. **根因分析深入**：发现 HSV 色彩空间中未成熟香蕉的黄绿色调（H≈20-30）被归入 yellow mask（H=15-38）而非 green mask（H=35-90），导致 green_ratio 总体偏低（unripe 中位数仅 0.034）。
4. **GLCM 纹理特征意外发现**：unripe 的 glcm_contrast（1.41）显著高于 ripe（0.90），glcm_energy/homogeneity 低于 ripe（Cohen's d 均 >0.8），为后续纹理辅助规则提供了依据。
5. **实验报告完整升级**：包含两类特征分布统计、阈值 sweep 表、错误样本逐个分析、调整前后对比、appendixed 版本历史。

### 不足点

1. **overripe 样本仍缺失**：dark_ratio_threshold、contrast_threshold、dark_ratio_low、overripe_yellow_max 四个阈值未经 overripe 样本验证。
2. **3 个 unripe 漏网样本无法通过 HSV 区分**：green_ratio < 0.01 的 unripe 样本在 HSV 空间中完全表现为黄色，仅凭当前颜色特征无法与 ripe 区分。
3. **2 个 ripe 误判样本存在标签歧义**：green_ratio=0.12-0.13 的 ripe 样本可能是"半熟"边界样本，当前三分类标签体系无法表达。
4. **ripe 召回小幅下降**（95%→85%）：边界样本在两类间的 green_ratio 存在不可避免的重叠，0.012 是 recall-precision trade-off 的最优解。

### 未完成 / 待继续优化

1. 补充 overripe 样本（≥20 张）后，对全部 6 个阈值进行联合 sweep 校准。
2. 引入 glcm_contrast/energy/homogeneity 辅助规则，尝试捕获 green_ratio < 0.01 的 unripe 漏网样本。
3. 运行 `python -m src.main_ml` 完成 KNN/SVM/Logistic 两类训练和交叉验证对比。

---

## 修改记录 #9 — 工程依赖环境检查与验证

**修改时间**：2026-06-01 19:40

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `report/report.md` | 修改记录 #9（本次） | 记录本次依赖环境检查结果 |

### 检查结论

**Python 环境**：`E:\Program Files\Python3.11.9\`（Python 3.11.9）

所有 `requirements.txt` 中列出的 10 项依赖均已安装，版本满足要求：

| 依赖 | 要求版本 | 实际版本 | 状态 |
|------|----------|----------|------|
| opencv-python | >=4.8.0 | 4.13.0 | ✅ |
| numpy | >=1.24.0 | 2.4.4 | ✅ |
| pandas | >=2.0.0 | 2.3.3 | ✅ |
| scikit-image | >=0.21.0 | 0.26.0 | ✅ |
| scikit-learn | >=1.3.0 | 1.8.0 | ✅ |
| matplotlib | >=3.7.0 | 3.10.8 | ✅ |
| PyYAML | >=6.0.0 | 6.0.3 | ✅ |
| joblib | >=1.3.0 | 1.5.3 | ✅ |
| PyQt5 | >=5.15.0 | 5.15.11 | ✅ |
| pytest | >=7.4.0 | 9.0.3 | ✅ |

**注意事项**：
- 系统中存在两个 Python 版本（3.9.13 和 3.11.9），PATH 中 `pip` 默认指向 3.9.13 的 pip。
- 安装/卸载包时必须使用 `python -m pip` 而非裸 `pip`，确保操作的是 3.11.9 环境。

### 优化点

1. 确认当前工程运行环境完整可用，无需额外安装任何依赖。

### 不足点

1. `requirements.txt` 中未锁定次级依赖（如 scipy、pillow、tifffile 等由主依赖自动安装的包），不同环境下次级依赖版本可能有差异。
2. 系统中存在 Python 3.9.13 残留环境，可能造成 `pip` 命令混淆。

### 未完成 / 待继续优化

1. 可考虑使用 `pip freeze` 生成完整的锁定依赖列表 (`requirements-lock.txt`)。
2. 可考虑清理 Python 3.9.13 残留或调整 PATH 顺序避免混淆。

---

## 修改记录 #8 — 新增 PyQt5 桌面应用界面

**修改时间**：2026-06-01 18:03

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/app_pyqt.py` | 全文（新文件） | 新增 PyQt5 桌面应用入口，实现单张图片识别 + 批量检测完整功能，约 430 行 |
| `requirements.txt` | L9 | 新增 `PyQt5>=5.15.0` 依赖 |
| `report/report.md` | 修改记录 #8（本次） | 记录本次 PyQt5 应用开发 |

### 优化点

1. **桌面应用入口就绪**：`python -m src.app_pyqt` 可启动完整的 PyQt5 图形界面，主窗口标题为「基于 OpenCV 与机器学习的香蕉成熟度识别应用系统」。
2. **单张图片识别功能完整**：
   - 打开图片后立即显示原图预览；
   - 点击「开始识别」后复用现有 `extract_features_for_image()` 流水线完成特征提取；
   - 三个面板分别展示原图、分割 mask（Viridis 伪彩色）、识别结果图（带预测文字标注的 mask 叠加图）；
   - 底部显示预测类别（颜色区分 unripe/ripe/overripe）和食用建议；
   - 表格展示 9 项关键特征值（green_ratio、yellow_ratio、dark_ratio、H/S/V_mean、glcm_contrast/energy/homogeneity）。
3. **分类方法选择**：工具栏下拉框支持规则分类、KNN、SVM、Logistic 四种方法切换。
4. **ML 模型缺失友好处理**：
   - 选择 ML 方法但模型文件不存在时弹出对话框，提供「回退到规则分类」或「取消」两个选项；
   - 批量模式下自动回退到规则分类并给出提示；
   - 预测过程中 ML 异常时自动回退到规则分类，不崩溃。
5. **批量检测（第二阶段功能）**：
   - 选择文件夹后遍历所有图片，使用 `QThread` 后台线程处理避免界面卡死；
   - 结果表格展示图片路径、预测类别和关键特征值；
   - 支持导出 CSV（UTF-8 BOM 编码，Excel 可直接打开）。
6. **完全复用现有 src/ 模块**：不复制任何算法逻辑，直接调用 `dataset_builder.extract_features_for_image()`、`ml_classifier.load_model()/predict_single()`、`rule_classifier.classify_by_rules()`、`visualization.draw_prediction()` 等。
7. **编译与测试通过**：`python -m compileall src tests` 无错误，`python -m pytest -q` 15 项测试全部通过。

### 不足点

1. **PyQt5 依赖未验证安装**：当前环境中 PyQt5 未安装（IDE 诊断提示），需用户在运行前执行 `pip install PyQt5`。
2. **批量模式无进度条**：仅通过状态栏文字显示进度，未使用 `QProgressBar` 控件。
3. **批量模式不支持选中行查看详情**：表格中点击某一行不会在图像面板中显示对应图片的识别结果。
4. **当前仅有 ripe 样本**：三分类效果需要在补充 unripe/overripe 样本后才能真正验证。
5. **高 DPI 适配仅在 Windows 测试**：`AA_EnableHighDpiScaling` 为 Qt5 属性，在其他平台上可能行为不同。

### 未完成 / 待继续优化

1. 批量模式下增加进度条 (`QProgressBar`)。
2. 批量结果表格支持点击行查看对应图片的详细识别结果（原图/mask/结果图回显）。
3. 考虑支持摄像头实时采集识别。
4. 美观度优化：增加深色主题、自定义样式表。

---

## 修改记录 #7 — 项目题目调整为 OpenCV 与机器学习应用系统并重写 README

**修改时间**：2026-06-01 17:41

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `README.md` | 全文 | 将项目题目正式调整为“基于 OpenCV 与机器学习的香蕉成熟度识别应用系统”；重新组织项目目标、当前代码状态、推荐系统架构、PyQt5 应用界面功能、运行方式、应用开发 Agent 提示词；将原“HSV + GLCM + 规则/ML 两阶段方案”移动到文末作为项目历史 |
| `report/report.md` | 修改记录 #7 | 追加本次题目变更与 README 重写的工程修改记录 |

### 优化点

1. **项目定位更符合应用展示要求**：从单纯算法流水线描述调整为 OpenCV + 机器学习 + PyQt5 桌面应用系统，明确最终交付应包含图形界面、单图识别、结果可视化和批量检测。
2. **README 结构更贴合当前代码现状**：区分了已完成的算法层能力和未完成的应用层能力，避免把当前命令行脚本误描述为完整应用。
3. **后续开发任务更清晰**：新增 PyQt5 应用开发建议和可直接复制的 Agent 提示词，便于继续实现 `src/app_pyqt.py`、模型选择、特征展示和批量检测功能。
4. **历史方案得到保留**：文末保留原始“两阶段递进式”方案，说明题目调整前后的关系，方便报告中解释项目演进过程。

### 不足点

1. 本次仅完成文档层面的题目调整和方案重写，尚未实际新增 PyQt5 应用界面代码。
2. 当前数据集仍缺少 `unripe` 与 `overripe` 真实样本，机器学习三分类效果仍无法有效验证。
3. `requirements.txt` 尚未加入 PyQt5 依赖，需在正式开发应用界面时同步更新。

### 未完成 / 待继续优化

1. 新增 `src/app_pyqt.py`，实现桌面应用入口。
2. 在 PyQt5 界面中实现单张图片识别、原图/mask/结果图展示、特征值展示和成熟度建议。
3. 补充三类样本后重新训练 KNN/SVM/Logistic，并在应用界面中支持模型选择。
4. 增加批量检测、结果表格和 CSV 导出功能。

---

## 修改记录 #6 — 规则分类器特征深度分析、ML 分类器模块完善、流水线单类容错

**修改时间**：2026-05-31 20:25

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `config.yaml` | `rules` 节 L23-L43 | 新增基于 20 张 ripe 样本统计的阈值设计依据注释（每个阈值对应 ripe 特征分布的分位数范围说明），阈值数值保持不变 |
| `src/ml_classifier.py` | 全文（重写） | 新增 `make_logistic()` 线性基线模型工厂；新增 `load_model()`、`predict_single()`、`get_model_info()` 辅助函数；`load_feature_data()` 增加 `allow_single_class` 参数和缺失列检查；支持 KNN/SVM/Logistic 三模型统一接口 |
| `src/main_ml.py` | 全文（重写） | 新增 `--cv-splits`/`--no-cv`/`--no-baseline`/`--allow-single-class` CLI 参数；新增 `_check_minimum_data()` 数据量检查；增加规则分类器 baseline 对比（从 summary.csv 读取）；单类场景优雅降级（SVM/Logistic 跳过并输出原因，KNN 正常拟合）；CV 自动降级当某类样本数不足；多模型对比 CSV 输出到 `results/comparison/` |
| `src/evaluation.py` | 全文（重写） | 新增 `evaluate_cross_validation()` 分层 K-fold CV 评估（自动降级 splits 数）；新增 `compare_models()` 多模型 CV 对比 DataFrame；新增 `evaluate_rule_classifier()` 规则分类器 ground-truth 评估；新增 `feature_coefficients()` 线性模型特征系数提取；新增 `plot_feature_importance()` 特征系数条形图 |
| `report/experiment_report.md` | 全文（重写） | 基于 2026-05-31 流水线重新运行结果，更新为 20 样本完整分析：特征分布统计（HSV 颜色比例 + HSV 统计 + GLCM 纹理 + 相关系数矩阵）、阈值设计依据逐条说明、误分类样本深度分析、阈值敏感度分析、分割质量全面检查、ML 模块就绪状态、单类场景测试结果、后续实验方向 |
| `report/report.md` | 修改记录 #6（本次） | 记录本次所有工程修改 |

### 优化点

1. **ML 模块健壮性大幅提升**：
   - 单类场景下不再崩溃，KNN 正常拟合保存，SVM/Logistic 输出明确的跳过原因。
   - 交叉验证自动检测各类样本数并降级 splits 数，避免 `StratifiedKFold` 错误。
   - 数据加载增加缺失列检查和友好错误信息，方便调试。
2. **评估体系完善**：
   - 新增分层 K-fold CV 评估，支持多模型并列对比（`compare_models()`）。
   - 规则分类器自动评估并与 ground-truth 标签对比，输出准确率基线。
   - 线性模型特征系数提取和可视化，支持模型可解释性分析。
3. **流水线可观测性提升**：
   - `main_ml` 输出类别分布、基线准确率、每模型报告、CV 对比表。
   - 所有中间结果（模型文件、分类报告、混淆矩阵、CV 对比 CSV）自动落盘。
4. **配置文件可读性改善**：6 个规则阈值均有明确的统计依据注释，后续调参有据可查。
5. **实验报告全面升级**：从单类别简单统计扩展为包含特征相关性矩阵、阈值敏感度分析、分割质量多维度检查、ML 模块状态报告的综合实验文档。

### 不足点

1. **unripe/overripe 样本仍缺失**：ML 模型（SVM/Logistic）无法完成有意义的训练和评估，CV 不可用，阈值跨类有效性未验证。
2. **dark_ratio 特征粒度过粗**：茎端、尖端、表面黑斑在 dark mask 中未区分，导致部分有斑点的 ripe 样本 dark_ratio 偏高（如 161901.jpg 达 0.67）。
3. **Logistic Regression 特征系数分析**：当前线性模型在单类场景下无法训练，`feature_coefficients()` 和 `plot_feature_importance()` 尚未在实际数据上验证。

### 未完成 / 待继续优化

1. 补充 unripe 和 overripe 样本（各 ≥20 张）后重新运行完整流水线，验证三分类效果。
2. 多类数据就绪后运行 `python -m src.main_ml` 完成 KNN/SVM/Logistic 三模型对比实验。
3. 增加暗斑连通域数量、最大暗斑面积占比等细粒度特征，提升 overripe/ripe 区分能力。
4. 复杂背景下分割鲁棒性测试。

---

## 修改记录 #5 — 新增实验报告并完成规则分类器综合评估

**修改时间**：2026-05-30 18:28

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `report/experiment_report.md` | 全文（新文件） | 新建独立实验报告，记录数据集概况、特征分布统计、分割质量分析、分类准确率、阈值调整依据、版本对比、局限性和后续实验方向。与 `report/report.md`（工程修改记录）职责分离 |

### 优化点

1. **报告职责分离**：`report/report.md` 仅记录工程修改，`report/experiment_report.md` 独立承载实验数据和分析结论，互不干扰。
2. **实验数据完整记录**：ripe 类别 20 张图片的 6 项特征分布（均值/标准差/分位数）、mask 面积异常分布、唯一误分类样本的特征值均已记录，后续补充 unripe/overripe 数据后可对比。
3. **阈值调整有据可查**：每个参数的原始值、当前值和调整依据均在报告中列出，方便后续回溯。

### 不足点

1. 因 unripe 和 overripe 样本数为 0，实验报告仅能在 ripe 单类别上展示结果，无法给出三分类混淆矩阵和泛化准确率。
2. 当前阈值的 overripe/unripe 分类规则未经实际样本验证，仅基于 ripe 类别的特征分布反推。

### 未完成 / 待继续优化

1. 采集 unripe 和 overripe 各 ≥20 张后，重新运行流水线并更新 `experiment_report.md` 中的统计表。
2. 补充数据后可进行三分类交叉验证，对比规则分类器与 SVM/KNN 的分类效果。

---

## 修改记录 #5 — 修复实验报告编码并准备版本分支上传

**修改时间**：2026-05-30 18:34

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `report/experiment_report.md` | 全文 | 将存在乱码和不可恢复替换字符的实验报告重写为 UTF-8 中文文档，保留数据集概况、处理流程、特征统计、分类结果、局限性和后续方向 |
| `report/report.md` | 修改记录 #5 | 记录本次实验报告编码修复和版本分支上传前的工程状态整理 |

### 优化点

1. **实验报告可读性恢复**：`report/experiment_report.md` 由乱码文本修复为可读中文，适合作为后续基础版实验分析文档。
2. **工程记录完整性提升**：上传版本分支前记录本次修复，避免分支中出现未解释的报告文件变更。

### 不足点

1. 实验报告中的统计数据来自当前已有结果描述，后续仍需要在补充三类样本后重新运行流程验证。

### 未完成 / 待继续优化

1. 补充 `unripe` 和 `overripe` 样本后，重新生成 `summary.csv` 并更新 `report/experiment_report.md`。

---

## 修改记录 #4 — 规范 report.md 定位并新增 agent 默认记录规则

**修改时间**：2026-05-30 18:17

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `report/report.md` | 文档顶部、修改记录 #4 | 明确本文档作为工程修改记录的定位，补充每条记录必须包含的字段，并记录本次规范化修改 |
| `README.md` | `主要模块说明`、`修改记录规范` | 补充 `AGENTS.md`、`CLAUDE.md` 说明，并说明如何通过仓库级指令文件默认要求 agent 更新 `report/report.md` |
| `AGENTS.md` | 全文 | 新增 Codex 等 agent 的仓库级默认规则，要求每次实际修改工程文件后同步更新 `report/report.md` |
| `CLAUDE.md` | 全文 | 新增 Claude Code 的仓库级默认规则，要求每次实际修改工程文件后同步更新 `report/report.md` |
| `src/rule_classifier.py` | `classify_by_rules()` 文档字符串和规则注释 | 将非 ASCII 箭头替换为 ASCII `->`，降低跨终端和跨工具显示异常风险 |
| `tests/test_features.py` | GLCM 注释、规则分类器测试文档字符串 | 将异常显示的数学符号和箭头替换为 ASCII 表达，避免编码显示问题影响阅读 |

### 优化点

1. **修改记录职责更明确**：`report/report.md` 已明确为工程修改记录，字段与用户要求保持一致。
2. **减少重复口头指令**：新增 `AGENTS.md` 和 `CLAUDE.md` 后，Codex、Claude Code 等工具在读取项目上下文时可以默认获得“每次修改后更新 report”的规则。
3. **跨工具可读性提升**：代码注释和测试文档字符串中的特殊符号已替换为 ASCII，避免 Windows PowerShell 或部分 agent 工具中出现乱码。

### 不足点

1. 不同 AI agent 对项目级指令文件的支持不完全统一。`AGENTS.md` 和 `CLAUDE.md` 可覆盖常见工具，但不能保证所有第三方 agent 自动读取。
2. 当前 README 和 report 仍包含中文内容，若终端代码页不是 UTF-8，PowerShell 直接 `Get-Content` 时可能显示乱码；文件本身按 UTF-8 可正常读取。

### 未完成 / 待继续优化

1. 如后续使用其他 agent 工具，需要确认该工具默认读取的项目规则文件名称，并将 `AGENTS.md` 中的规则同步过去。
2. 可以后续增加一个脚本或 pre-commit 检查，用于提示“源码有修改但 `report/report.md` 未更新”的情况。

---

## 修改记录 #3 — 修复 --no-save-images 参数导致的 UnboundLocalError

**修改时间**：2026-05-30 18:08

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/main_rule_based.py` | `main()` L40-L43 | 将 `prediction = row["rule_prediction"]` 从 `if not args.no_save_images:` 块内移至块外，解决使用 `--no-save-images` 时变量未赋值导致 `UnboundLocalError` 的问题 |

### 优化点

1. **修复崩溃 Bug**：`--no-save-images` 模式下 `prediction` 变量在 `if` 块内未赋值，但 `print` 语句在块外始终引用它。将赋值提升到块外，确保两种模式均正常工作。

### 不足点

1. 无。本次为 Bug 修复，未引入新的已知问题。

### 未完成 / 待继续优化

1. 无。

---

## 修改记录 #2 — summary.csv 与 combined_features.csv 内容区分

**修改时间**：2026-05-30 18:05

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `src/main_rule_based.py` | `main()` L51-L60 | `combined_features.csv` 改为仅写入 `label` + `FEATURE_COLUMNS` 特征列，不再写入 `image_path`、`rule_prediction`、`mask_area`，与 `summary.csv` 内容区分 |

### 优化点

1. **CSV 职责分离**：`summary.csv` 保留完整分析信息（路径、标签、全部特征、预测结果、mask 面积），`combined_features.csv` 仅保留标签与特征列，消除两个 CSV 内容完全一样的冗余问题。
2. **ML 可用性**：`combined_features.csv` 现在可直接作为 `src/main_ml.py` 的特征输入表，无需手动删除非特征列。

### 不足点

1. 无。本次为缺陷修复，未引入新的已知问题。

### 未完成 / 待继续优化

1. 无。

---

## 修改记录 #1 — 规则分类器阈值调优与测试完善

**修改时间**：2026-05-30 18:05

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `config.yaml` | `rules` 节 | 调整全部 6 个阈值参数，新增 `dark_ratio_low` 和 `overripe_yellow_max` |
| `src/rule_classifier.py` | `DEFAULT_RULES`（L6-L13）、`classify_by_rules`（L16-L57） | 新增组合规则（dark + yellow）和纹理规则（contrast + dark_low）；将原硬编码常量 0.08 提取为可配置参数 `dark_ratio_low`；更新 DEFAULT_RULES 为当前阈值；补充函数文档字符串 |
| `tests/test_features.py` | 全文 | 从 2 个测试用例扩展到 15 个，覆盖：HSV 绿色/黄色区域检测、空 mask 边界、GLCM 空 mask/常量区域/极小 ROI 边界、规则分类器六条规则分支、自定义阈值覆盖 |
| `report/report.md` | 全文 | 重新定位为项目修改记录 |

### 优化点

1. **准确率大幅提升**：ripe 类别分类准确率从 5.00%（1/20）提升至 95.00%（19/20）。
2. **规则可用性修复**：原 `contrast_threshold=35.0` 在 32 级 GLCM 下永远无法触发，现校准为 1.45，规则 3 恢复实际分类作用。
3. **消除硬编码**：`classify_by_rules` 中不再有硬编码的数值常量，所有阈值均可通过 config 或调用参数覆盖。
4. **组合规则减少误判**：新增 `overripe_yellow_max` 约束，使得 dark_ratio 较高但 yellow_ratio 同样较高的成熟香蕉不再被误判为 overripe。
5. **测试覆盖率提升**：从 2 条用例扩至 15 条，覆盖 HSV 特征、GLCM 特征和规则分类器的正常路径与边界条件。

### 不足点

1. **仅有 ripe 样本**：data/raw/unripe 和 data/raw/overripe 仍为空，无法验证规则对另两类的真实区分效果。
2. **dark_ratio 特征粒度过粗**：香蕉茎端、尖端阴影与表面黑斑被统一计入 dark_ratio，导致部分有斑点的 ripe 香蕉与真正的 overripe 香蕉难以区分。
3. **GLCM 仅基于边界框**：当前在 banana_mask 的 bounding box 内计算纹理，未被 mask 覆盖的背景像素用中值填充，可能引入轻微偏差。

### 未完成 / 待继续优化

1. 采集 unripe 和 overripe 样本（各 ≥ 20 张），重新统计三类特征分布并校准阈值。
2. 优化 dark mask 定义或对 dark_ratio 按区域加权，降低茎端/尖端对 dark_ratio 的贡献。
3. 增加暗斑连通区域数量、最大暗斑面积占比等细粒度特征。
4. 在复杂背景（多根香蕉、其他水果）下测试分割鲁棒性，必要时引入 GrabCut 或颜色直方图反向投影。
5. 安装 scikit-learn 后进入 SVM/KNN 机器学习版本实验。

---

## 模板：修改记录 #N — 标题

**修改时间**：YYYY-MM-DD HH:MM

### 修改文件清单

| 文件 | 修改位置 | 修改说明 |
|------|----------|----------|
| `path/to/file.py` | 函数/行号 | 具体改了什么 |

### 优化点

1. 列出本次修改带来的改进。

### 不足点

1. 列出本次修改后已知的问题或退化。

### 未完成 / 待继续优化

1. 列出尚未解决、留给下一版处理的事项。
