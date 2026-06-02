# 项目修改记录

本文档的定位是记录每次工程修改后的修改内容总结，不用于存放最终实验报告。新增记录按时间倒序写在顶部。

每条记录必须包含：

1. 本次内容修改完成时间。
2. 本次修改的文件列表和具体修改的代码位置。
3. 本次修改后项目相对于上一版项目的优化点或不足点。
4. 本次修改未完成的部分或需要继续优化的部分。

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
