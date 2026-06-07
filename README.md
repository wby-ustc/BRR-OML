# 基于 OpenCV 与机器学习的香蕉成熟度实时识别应用系统

本项目面向香蕉成熟度识别的课程/实验应用开发，目标是从“图像处理算法流水线”升级为一个可交互的桌面应用系统，并进一步扩展为支持笔记本电脑前置摄像头的实时识别系统。系统使用 OpenCV 完成图像预处理、香蕉主体分割、HSV 颜色特征与 GLCM 纹理特征提取，并结合规则分类器和机器学习模型判断香蕉成熟度。

当前项目题目：

> 基于 OpenCV 与机器学习的香蕉成熟度实时识别应用系统

推荐英文题目：

> Real-time Banana Ripeness Recognition Application System Based on OpenCV and Machine Learning

推荐缩写：

> BRR-RT

## 当前目标

当前项目建议从“图片上传识别 + 批量检测”的 PyQt5 桌面应用，升级为“图片识别 + 批量检测 + 摄像头实时识别”的综合应用系统。最终系统建议包含：

- PyQt5 图形化桌面界面。
- 单张图片上传与成熟度识别。
- 批量图片检测与 CSV 导出。
- 笔记本电脑前置摄像头实时采集与识别。
- 原图、分割 mask、识别结果图同步展示。
- HSV 颜色比例与 GLCM 纹理特征展示。
- 规则分类与 KNN/SVM/Logistic 机器学习分类结果展示。
- 摄像头实时模式下的暂停、继续、截图识别和结果稳定显示。
- 分类准确率、混淆矩阵和实验报告展示。

成熟度类别设计为三类：

- `unripe`：未成熟，表面以绿色或黄绿色为主。
- `ripe`：成熟，表面以黄色为主，黑斑较少。
- `overripe`：过熟，表面存在明显黑斑、褐色区域或整体颜色变暗。

## 前置摄像头可行性评估

将笔记本电脑前置摄像头作为香蕉成熟度识别摄像头是可行的，适合作为课程设计、实验展示和原型系统演示。当前项目已有 OpenCV、PyQt5、规则分类器和特征提取模块，摄像头功能主要需要新增“视频帧采集、帧级推理、实时显示和性能控制”的应用层代码，不需要推翻现有算法方案。

可行性依据：

- OpenCV 原生支持 `cv2.VideoCapture(0)` 读取笔记本默认摄像头。
- 当前算法层已经以 OpenCV BGR 图像数组为核心处理对象，预处理、分割、HSV 特征、GLCM 特征和可视化逻辑可以复用。
- PyQt5 当前已用于桌面界面，适合通过 `QTimer` 或 `QThread` 实现实时画面刷新。
- 规则分类器不依赖训练模型文件，适合作为实时识别第一版的默认分类方法。
- KNN/SVM/Logistic 模型可在训练完成后作为可选实时分类方法加载。

主要限制：

- 笔记本前置摄像头像素、动态范围和对焦能力通常弱于手机或外接摄像头。
- 自动曝光和自动白平衡会改变 HSV 特征，可能影响阈值分类稳定性。
- 摄像头画面容易出现复杂背景、手部遮挡、运动模糊和距离变化。
- 当前规则阈值基于静态图片数据校准，实时摄像头场景可能需要重新调参。
- GLCM 特征计算比颜色特征更耗时，实时模式不宜每帧都完整推理。

结论：

- **演示和课程验收层面：可行**。建议先实现规则分类实时识别，强调可交互应用系统能力。
- **稳定实际部署层面：需要补充摄像头采集样本重新验证**。若追求更稳定效果，建议固定光照、纯色背景、固定距离，或使用外接摄像头。

## 当前代码状态

当前工程已经具备以下能力：

- OpenCV 图像读取、缩放、滤波和亮度归一化。
- HSV 颜色空间分割。
- 形态学开闭运算与最大连通区域提取。
- HSV 颜色比例特征提取。
- GLCM 纹理特征提取。
- 基于人工阈值的规则分类器。
- KNN、SVM、Logistic Regression 机器学习分类器代码。
- 分类报告、混淆矩阵、交叉验证和模型对比代码。
- mask、标注图、对比图、CSV 结果输出。
- PyQt5 桌面应用入口 `src/app_pyqt.py`。
- 单张图片识别、批量检测和 CSV 导出。
- 基础测试用例。

当前已具备但需继续优化：

- 摄像头实时识别已提供基础版入口（`src/inference.py` + `src/app_pyqt.py` 摄像头模式），支持打开/关闭/暂停/截图和实时三栏显示。
- 帧级推理封装 `src/inference.py` 已实现，含严格香蕉候选区域验证和多帧稳定性投票。
- **摄像头模式使用独立的 `camera_rules` 规则阈值和 `camera_preprocessing` 白平衡**，与静态图片 `rules` 分离，针对性解决摄像头场景下 ripe 召回偏低和光照敏感问题（详见 `config.yaml` 注释）。
- 进阶版界面分类方法已开放”规则分类”、”KNN”、”SVM”和”Logistic”。
- 图像显示已改为按标签尺寸缩放，窗口缩放时自动铺满显示框。
- 单图和摄像头实时模式已能显示 ML 概率/置信度，KNN/SVM/Logistic 均支持模型过期检查和规则分类回退。

当前仍未完成或需要继续优化：

- **摄像头 `camera_rules` 阈值为推理值**：`green_ratio_threshold=0.06`、`contrast_high=2.20`、`yellow_ratio_threshold=0.40` 等基于摄像头物理特性推导，已通过模拟验证（ripe 典型值 0.03→unripe 修正为 ripe），但尚未在真实多场景摄像头数据上进行系统化准确率评估和网格搜索调优。
- **白平衡基于简单百分位拉伸**：`simple_white_balance()` 使用 per-channel 1%/99% 百分位拉伸，对极端光照（背光、强侧光、混合色温）的校正能力有限，尚未与更复杂的方法（Gray World、Retinex）对比。
- 多帧稳定性投票的 `confirm_frames` / `lost_frames` 参数尚未在摄像头实采数据上做系统调优。
- KNN/SVM/Logistic 虽已开放，但仍主要基于静态图片样本训练，摄像头真实环境泛化能力尚未系统评估。
- 批量检测表格当前仍以单一预测结果为主，尚未逐条显示实际方法、置信度和多模型对比结果。
- 摄像头实时模式尚未实现多帧概率平滑，ML 概率可能随光照和分割噪声轻微波动。

## 基础版剩余优化方案（最新样本替换后）

当前 `data/raw/overripe/` 已加入 10 张新的过熟香蕉图片，`data/raw/unripe/` 已加入 7 张新的未成熟香蕉图片，用于替代上一轮效果不理想的网络图片。当前三类目录各 26 张样本，样本数量保持平衡，但特征分布已经相对上一轮发生变化。因此基础版下一步不建议继续直接手调摄像头阈值，而应先完成“最新样本复测 -> 摄像头实采校准 -> 界面鲁棒性提示”的闭环。

### 1. 最新样本复测与模型刷新

目标：确认新加入的过熟、未成熟样本是否改善静态图片识别，并同步更新 KNN 基础模型。

建议步骤：

1. 运行 `python -m src.main_rule_based --input data/raw --config config.yaml`，重新生成三类样本的规则分类结果和 `data/features/combined_features.csv`。
2. 统计三类准确率、召回率和混淆矩阵，重点检查：
   - 新增 10 张 `overripe` 是否仍被误判为 `ripe` 或 `unripe`。
   - 新增 7 张 `unripe` 是否仍被误判为 `ripe`。
   - `ripe` 类是否因为 `camera_rules` 或静态 `rules` 的差异受到间接影响。
3. 运行 `python -m src.main_ml --config config.yaml`，基于最新 `combined_features.csv` 重新训练 KNN/SVM/Logistic，并保留基础版界面只开放 KNN。
4. 将新的准确率、混淆矩阵和失败样本原因写入 `report/experiment_report.md`，不要只保留模型分数。

优化原因：

- 新样本替换会改变 HSV/GLCM 特征分布，旧阈值和旧模型不能直接视为已验证。
- 基础版实时识别若继续使用旧 KNN，会让单图、批量和摄像头截图三条路径的判断依据不一致。

### 2. 摄像头真实场景校准

目标：针对“被其他物体或人干扰”“无法识别到香蕉”“光照导致成熟度误判”的问题，用真实摄像头数据校准基础版规则。

建议步骤：

1. 额外采集摄像头环境样本，每类至少 20 张，覆盖以下场景：
   - 白纸/浅色桌面背景。
   - 普通室内背景。
   - 暖光、冷光、背光、侧光。
   - 手部短暂遮挡。
   - 无香蕉但有人、衣服、桌面、屏幕等干扰物。
2. 复用 `src/inference.py` 的帧级推理逻辑，离线批量评估摄像头截图，不要每次只凭实时画面主观判断。
3. 对 `config.yaml` 中三组摄像头参数做网格搜索：
   - `candidate`：优先调 `min_banana_color_ratio`、`min_yellow_green_ratio`、`max_dark_ratio_for_presence`、`min_extent`、`use_center_roi`。
   - `camera_rules`：优先调 `green_ratio_threshold`、`yellow_ratio_threshold`、`dark_ratio_threshold`、`contrast_high`。
   - `stability`：对比 `confirm_frames=2/3/4`、`lost_frames=2/3/4` 的响应速度和误检率。
4. 将最优参数只写入 `config.yaml`，不要把针对摄像头的经验阈值硬编码到 Python 文件。

优化原因：

- 其他物体和人造成的误检主要发生在“候选区域是否像香蕉”阶段，应优先调 `candidate`，而不是只调成熟度分类规则。
- 光照造成的成熟度误判主要发生在颜色比例和纹理特征阶段，应调 `camera_preprocessing` 和 `camera_rules`。
- 多帧投票可以降低画面抖动造成的类别跳变，但会增加响应延迟，需要用实采数据权衡。

### 3. 基础版界面鲁棒性增强

目标：让用户知道系统为什么没有识别到香蕉，并减少使用方式导致的误判。

建议步骤：

1. 在摄像头模式的信息区显示 `candidate_reason`，例如“目标不在画面中心区域”“暗色占比过高”“香蕉颜色占比过低”。
2. 在界面中显示当前使用的规则集：静态图片使用 `rules`，摄像头使用 `camera_rules`。
3. 增加简短状态提示：建议香蕉放在画面中心、使用浅色背景、避免背光。
4. 对“未检测到香蕉”和“检测到香蕉但成熟度低置信”的显示做区分，避免用户把分割失败理解为分类错误。
5. KNN 加载时读取模型元数据，若 `combined_features.csv` 比模型训练时间更新，提示重新训练。

优化原因：

- 当前基础版算法仍以 HSV/GLCM 和规则阈值为核心，无法像深度学习检测器一样天然识别所有复杂背景中的香蕉。
- 明确失败原因可以帮助用户调整摆放位置和光照，也方便后续收集问题样本。

### 4. 基础版边界与进阶版预留

基础版建议继续保持“规则分类 + KNN”为主要演示能力，不急于开放 SVM/Logistic。SVM/Logistic 可作为进阶版对比模型，在以下条件满足后再开放：

- 每类静态样本不少于 50 张。
- 每类摄像头环境样本不少于 20 张。
- 有独立验证集或至少三折交叉验证报告。
- UI 已能清楚说明模型文件是否过期、类别是否完整。

若基础版仍无法满足复杂背景下的香蕉定位需求，下一阶段再考虑引入 ROI 手动框选、背景减除或轻量目标检测模型；但这属于进阶方向，不应混入当前基础版的最小可验收范围。

## 基础版完成判断（误判样本替换后）

根据 `report/report.md` 中 #20、#21 记录，当前基础版已经达到进入进阶版“机器学习模型实时识别”阶段的条件：

- 静态样本复测已完成：三类各 25 张有效图片，规则分类总准确率为 74/75 = **98.67%**。
- overripe 与 unripe 的误判图片已经替换后复测：overripe 召回 **100%**，unripe 召回 **100%**。
- 仅剩 `ripe/banana-24.jpg` 这一张边界样本未替换：其 `green_ratio=0.028` 略高于静态规则阈值，属于 ripe/unripe 连续光谱上的边界 case，不建议为了消除单张错误而继续牺牲规则泛化性。
- KNN/SVM/Logistic 已基于更新后的 `combined_features.csv` 重新训练并生成模型元数据；报告中 SVM test accuracy 达到 100%，KNN/SVM/Logistic CV 均达到 94% 左右。
- 基础版 UI 已支持单图识别、批量检测、摄像头实时识别、候选验证失败原因显示、规则集名称显示、KNN 模型过期提示和多帧稳定性投票。

结论：**基础版方案可以视为已完成课程/实验验收层面的主要需求，可以进入进阶版开发**。后续不应再围绕单个静态边界样本反复调整规则阈值，而应把重点转向机器学习模型在实时摄像头场景中的可用性、置信度展示、模型管理和对比评估。

仍需保留的基础版边界说明：

- 当前准确率结论基于每类 25 张静态图片，样本规模仍偏小。
- 摄像头真实场景仍受光照、背景、距离、遮挡影响，进阶版 ML 也应继续保留候选验证和规则分类回退。
- 规则分类仍应作为默认兜底路径，不能因为开放 SVM/Logistic 而删除。

## 进阶版方案：机器学习模型实时识别

### 1. 目标定位

进阶版目标不是替代基础版规则分类，而是在现有实时摄像头链路上开放和比较 KNN/SVM/Logistic 三类机器学习模型，使系统具备以下能力：

- 摄像头实时模式可选择 `规则分类`、`KNN`、`SVM`、`Logistic`。
- 单图、批量、截图识别、摄像头实时识别使用统一的模型加载、类别完整性校验和回退逻辑。
- 实时界面显示模型预测概率、置信度、实际使用的方法和回退原因。
- 模型文件缺失、类别不完整、特征表已更新但模型未重训时，不崩溃，并明确提示用户。
- 在报告中形成规则分类与 KNN/SVM/Logistic 的对比结论。

### 2. 当前代码基础

当前代码已经为进阶版预留了关键能力：

- `src/ml_classifier.py` 已包含 `make_svm()`、`make_logistic()`、`validate_model_classes()`、`save_model_meta()`、`load_model_meta()`。
- `src/inference.py` 的 `METHOD_TO_MODEL` 已包含 `KNN`、`SVM`、`Logistic`，`predict_features()` 已支持模型缓存、类别完整性校验和规则分类回退。
- `src/app_pyqt.py` 的 `METHOD_TO_MODEL` 已包含三类 ML 模型，当前仅通过 `CLASS_METHODS = ["规则分类", "KNN"]` 在 UI 层隐藏 SVM/Logistic。
- `models/*_model_meta.json` 已记录类别、样本数、训练时间、特征表时间、test accuracy 和 CV accuracy。

因此进阶版第一步应以“小范围开放 + 状态显示 + 验证”为主，不需要重写图像处理、分割或帧级推理模块。

### 3. 实施步骤

#### 阶段 A：开放 SVM/Logistic 选择

修改建议：

1. 在 `src/app_pyqt.py` 中将 `CLASS_METHODS` 改为 `["规则分类", "KNN", "SVM", "Logistic"]`。
2. 保留 `METHOD_TO_MODEL` 映射，不删除规则分类兜底。
3. 单图、批量、截图、实时摄像头四条路径都继续调用已有模型存在性检查和 `validate_model_classes()`。
4. 模型无效时保留自动回退规则分类，并在状态栏或结果标签中显示回退原因。

验收重点：

- 切换到 SVM/Logistic 不应崩溃。
- 模型文件缺失时能提示并回退。
- 旧的单类别调试模型不能被加载为正式模型。

#### 阶段 B：显示概率和置信度

修改建议：

1. 对 KNN/SVM/Logistic 的预测结果显示 top-1 概率。
2. 在特征表或结果区新增 `模型置信度`、`概率分布`、`实际方法` 三项。
3. 设置置信度阈值，例如 `ml.min_confidence: 0.60`：
   - 若 top-1 概率低于阈值，显示“低置信”。
   - 低置信时不强行改判，但应同时显示规则分类结果供对比。
4. 对不支持稳定概率或概率不可用的模型，显示“概率不可用”，不要伪造概率。

验收重点：

- 用户能看出 SVM/Logistic 与规则分类是否一致。
- 低置信预测不会被包装成确定结论。

#### 阶段 C：模型状态管理

修改建议：

1. 将现有 `_check_knn_staleness()` 扩展为通用 `_check_model_staleness(method)`，支持 KNN/SVM/Logistic。
2. 在模型选择变化、打开摄像头、单图识别、批量检测完成时检查模型状态。
3. 在 UI 中显示：
   - 模型是否存在。
   - 模型类别是否完整。
   - 模型训练样本数和训练时间。
   - `combined_features.csv` 是否比模型更新。
4. 如果模型过期，提示运行 `python -m src.main_ml --config config.yaml`。

验收重点：

- 用户不会误用旧模型。
- 新增图片或重新生成特征表后，界面能提示重新训练。

#### 阶段 D：实时模型对比与报告输出

修改建议：

1. 在摄像头截图识别或单图识别中可选显示多模型对比：
   - 规则分类结果。
   - KNN 结果与概率。
   - SVM 结果与概率。
   - Logistic 结果与概率。
2. 批量检测结果表可增加不同模型预测列，方便导出后分析。
3. 在 `report/experiment_report.md` 中新增进阶版模型对比小节，记录：
   - 三类模型 test accuracy。
   - CV mean/std。
   - 与规则分类不一致的样本。
   - 实时摄像头测试中的典型成功/失败场景。

验收重点：

- 进阶版不仅“能选模型”，还要能解释模型差异。
- 报告能说明为什么某个模型适合作为实时默认模型。

### 4. 进阶版默认策略建议

短期建议：

- 默认实时方法仍保留 `规则分类`。
- KNN 作为基础 ML 对照方法。
- SVM/Logistic 在界面中开放，但标注为“进阶模型”。
- 当 SVM/Logistic 与规则分类一致且置信度高时，可作为增强结论；当不一致或低置信时，界面应显示“建议复核”。

中期建议：

- 若摄像头实采样本扩充到每类 50 张以上，并且 SVM/Logistic 在交叉验证和摄像头截图集上稳定优于规则分类，再考虑把 SVM 设为推荐实时模型。

不建议在当前阶段做的事：

- 不建议为了进阶版删除规则分类。
- 不建议在样本量仍有限时宣称 SVM/Logistic 泛化能力已经稳定超过规则分类。
- 不建议引入深度学习检测模型作为本轮进阶版核心，除非基础 ML 实时识别已经完成并有明确对比结果。

## 进阶版完成情况与后续优化方案

根据 `report/report.md` 中 #22 记录和当前 `src/app_pyqt.py`、`src/inference.py` 代码，进阶版第一轮“机器学习模型实时识别”已经完成主要功能：

- UI 分类方法已开放 `规则分类`、`KNN`、`SVM`、`Logistic`。
- 单图、批量、截图和摄像头实时路径均保留模型存在性检查、类别完整性校验和规则分类回退。
- 摄像头实时模式通过 `model_cache` 缓存 ML 模型，不会每帧重复加载。
- 单图和摄像头实时模式可显示 ML 概率/置信度；回退时能显示低置信或回退状态。
- `_check_model_staleness(method)` 已支持 KNN/SVM/Logistic 的模型过期检查。

因此，后续进阶版优化重点应从“开放模型”转向“结果可分析、实时稳定、报告可解释”。

### 1. 批量结果表格与 CSV 增强

目标：让批量检测结果不仅有预测类别，还能用于比较模型可靠性。

建议修改：

1. 在 `BatchWorker` 输出结果中增加：
   - `method_requested`：用户选择的方法。
   - `method_used`：实际使用的方法，包含回退原因。
   - `confidence`：top-1 概率，规则分类为空或 `N/A`。
   - `prob_overripe`、`prob_ripe`、`prob_unripe`：三类概率列。
2. 在批量结果表格中增加“实际方法”“置信度”列。
3. 在 CSV 导出字段中同步增加上述列，便于后续实验分析。
4. 当批量模式发生模型回退时，在表格中显示回退后的 `method_used`，不要只显示预测类别。

优化原因：

- 当前批量表格只显示单一预测结果，不足以判断 ML 是否正常生效。
- 进阶版报告需要对比规则/KNN/SVM/Logistic，批量 CSV 是最直接的数据来源。

### 2. 多模型并行对比

目标：让单图或截图识别能同时展示规则分类、KNN、SVM、Logistic 的结果，便于解释模型差异。

建议修改：

1. 新增一个轻量函数，例如 `predict_features_all_methods(features, config, model_cache)`，统一返回四种方法的预测、概率和状态。
2. 在单图识别和截图识别中增加“多模型对比”显示区或弹窗：
   - 规则分类结果。
   - KNN top-1 + 概率。
   - SVM top-1 + 概率。
   - Logistic top-1 + 概率。
3. 若某个模型缺失、过期或类别不完整，显示对应状态，不影响其他模型输出。
4. 多模型对比作为辅助分析功能，不改变主预测结果。

优化原因：

- 当前 UI 一次只能看一个方法，难以判断模型分歧。
- 对边界样本（如 `ripe/banana-24.jpg`），多模型对比能比单一硬分类更有解释力。

### 3. 置信度策略与实时平滑

目标：减少实时摄像头下 ML 概率跳动，避免把低置信结果显示为确定结论。

建议修改：

1. 在 `config.yaml` 新增：

```yaml
ml:
  min_confidence: 0.60
  smooth_window: 3
  show_model_comparison: false
```

2. 摄像头实时模式对最近 `smooth_window` 次 ML 概率做滑动平均，仅用于显示和稳定 top-1。
3. 当 top-1 概率低于 `min_confidence` 时：
   - 结果标签显示“低置信”。
   - 同时显示规则分类结果作为参考。
   - 不强制改判为规则分类，避免隐藏模型真实输出。
4. 对规则分类可增加“规则距离提示”，例如距离触发阈值很近时显示“边界样本”。

优化原因：

- 摄像头帧之间 HSV/GLCM 特征会因自动曝光和分割波动产生小幅变化。
- ML 概率比硬分类更敏感，需要平滑和阈值提示。

### 4. 模型元数据可视化

目标：让用户知道当前模型是否可信、是否过期、训练数据规模是多少。

建议修改：

1. 在 UI 中增加“模型状态”信息行或菜单项，显示：
   - 模型文件是否存在。
   - `classes` 是否包含三类。
   - `n_samples`、`class_counts`。
   - `test_accuracy`、`cv_accuracy`。
   - `train_time`。
2. 当用户切换分类方法时，立即更新模型状态。
3. 如果模型过期，将状态栏提示升级为更清晰的 UI 标签。

优化原因：

- 进阶版开放多个模型后，用户更容易误用旧模型或无效模型。
- 模型元数据已经存在，UI 展示成本低，收益高。

### 5. 摄像头实采评估

目标：验证静态图片训练出的 ML 模型在真实摄像头场景中的泛化能力。

建议步骤：

1. 建立 `data/camera_eval/` 或另行保存不提交 Git 的摄像头评估集，每类至少 20 张，另含无香蕉干扰图。
2. 复用 `src/inference.py` 离线跑摄像头截图，统计：
   - 香蕉候选检测通过率。
   - 三类成熟度准确率。
   - 规则/KNN/SVM/Logistic 分歧样本。
   - 低置信样本比例。
3. 将结论写入 `report/experiment_report.md`，不要只依赖 UI 实时观察。

优化原因：

- 当前模型训练和复测主要基于静态图片；摄像头环境的色偏、噪声和背景差异仍是最大风险。
- 进阶版是否能把 SVM 设为推荐模型，应以摄像头评估集结果为依据。

### 6. 推荐优先级

建议下一轮按以下顺序执行：

1. **先做批量结果表格与 CSV 增强**：风险低、收益高，直接支撑实验报告。
2. **再做多模型并行对比**：便于分析边界样本和模型分歧。
3. **再做置信度阈值与实时平滑**：需要更细 UI 和状态逻辑，适合在批量结果可分析后实施。
4. **最后做摄像头实采评估**：需要额外采样，不应与代码结构调整混在一次提交中。

## 推荐最新系统架构

```text
PyQt5 桌面应用界面
  -> 图片模式
      -> 单张图片选择
      -> OpenCV 图像预处理
      -> 香蕉主体区域分割
      -> HSV + GLCM 特征提取
      -> 规则分类器 / KNN / SVM / Logistic 预测
      -> 原图 + mask + 结果图 + 特征表 + 预测结果展示
  -> 批量模式
      -> 文件夹选择
      -> 批量特征提取与预测
      -> 结果表格展示
      -> CSV 导出
  -> 摄像头实时模式
      -> 打开笔记本前置摄像头
      -> 持续采集视频帧
      -> 按固定时间间隔进行帧级推理
      -> 实时显示摄像头画面、mask、识别结果图和特征值
      -> 支持暂停、继续、关闭摄像头和截图识别
```

建议保留现有 `src/app_pyqt.py` 作为桌面应用入口，并新增一个轻量的帧级推理模块：

```text
src/
├── app_pyqt.py
├── inference.py              # 建议新增：统一图片和摄像头帧推理
├── dataset_builder.py
├── preprocessing.py
├── segmentation.py
├── feature_hsv.py
├── feature_glcm.py
├── rule_classifier.py
├── ml_classifier.py
└── visualization.py
```

## 实时识别功能设计

### 1. 摄像头入口

界面控件建议：

- “打开摄像头”按钮。
- “关闭摄像头”按钮。
- “暂停/继续”按钮。
- “截图识别”按钮。
- “摄像头编号”下拉框，默认 `0`。
- “分类方法”下拉框：规则分类、KNN、SVM、Logistic。
- 原始摄像头画面显示区域。
- 分割 mask 显示区域。
- 识别结果图显示区域。
- 当前预测类别、食用建议和关键特征值表格。

实时流程：

```text
打开摄像头
-> cv2.VideoCapture(0) 获取视频帧
-> PyQt5 定时器或后台线程刷新画面
-> 每隔 inference_interval_ms 抽取一帧进行识别
-> 预处理、分割、提取 HSV + GLCM 特征
-> 规则分类或机器学习模型预测
-> 显示原始帧、mask、结果图、类别和特征值
-> 关闭摄像头时释放 VideoCapture
```

### 2. 帧级推理封装

当前 `src/dataset_builder.py` 中的 `extract_features_for_image()` 接收图片路径。实时识别不应把每一帧写入磁盘，建议新增 `src/inference.py`：

```text
extract_features_for_frame(frame_bgr, config)
predict_features(features, config, method, model_cache)
run_inference_on_frame(frame_bgr, config, method, model_cache)
```

推荐职责：

- `extract_features_for_frame()`：接收 OpenCV BGR 图像数组，复用预处理、分割、HSV 和 GLCM 特征提取。
- `predict_features()`：统一规则分类和 ML 分类。
- `run_inference_on_frame()`：返回 `processed_frame`、`mask`、`prediction`、`features`、`result_image`。

### 3. 实时性能策略

摄像头画面显示和识别计算应分开控制：

- 画面刷新：建议 20-30 FPS。
- 推理频率：建议 1-3 FPS，即每 300-1000 ms 推理一次。
- 实时识别尺寸：建议将最长边缩放到 640，而不是沿用静态图片的 900。
- 模型加载：ML 模型应在切换分类方法或启动摄像头时加载一次，不要每帧加载。
- UI 线程：摄像头采集和推理建议使用 `QThread`，避免界面卡顿。

### 4. 配置建议

建议在 `config.yaml` 中新增：

```yaml
camera:
  device_index: 0
  width: 1280
  height: 720
  display_fps: 30
  inference_interval_ms: 500
  realtime_max_size: 640
  mirror: false
```

参数说明：

- `device_index`：摄像头编号，笔记本前置摄像头通常为 `0`。
- `width` / `height`：摄像头采集分辨率。
- `display_fps`：界面刷新帧率。
- `inference_interval_ms`：识别间隔，控制性能和稳定性。
- `realtime_max_size`：实时推理缩放尺寸。
- `mirror`：是否镜像显示摄像头画面。

### 5. 实时模式验收标准

第一版摄像头实时识别应满足：

- 可通过 `python -m src.app_pyqt` 启动桌面应用。
- 点击“打开摄像头”后可显示笔记本前置摄像头画面。
- 将香蕉放到摄像头前时，界面能显示分割 mask 和识别结果图。
- 预测类别、食用建议和关键特征值能随画面定时更新。
- 点击“关闭摄像头”后能释放摄像头，不残留占用。
- 模型文件不存在时不崩溃，能够回退到规则分类或给出明确提示。
- 不破坏现有单图识别、批量检测、`main_rule_based.py` 和 `main_ml.py` 流程。

## 推荐实施步骤

### 阶段 1：规则分类实时识别 MVP

目标是快速验证摄像头实时链路。

修改建议：

- 新增 `src/inference.py`。
- 在 `src/app_pyqt.py` 增加摄像头按钮和实时显示区域复用逻辑。
- 使用 `cv2.VideoCapture(0)` 读取前置摄像头。
- 默认使用规则分类器。
- 每 500 ms 识别一次，画面可更高频刷新。
- 在 `report/report.md` 记录本次修改。

### 阶段 2：机器学习模型实时识别

目标是让实时模式支持 KNN/SVM/Logistic。

修改建议：

- 运行 `python -m src.main_ml` 基于最新 `combined_features.csv` 训练模型。
- 在应用启动或分类方法切换时缓存模型。
- 实时帧使用缓存模型预测，显示概率信息。
- 模型缺失时给出提示并回退到规则分类。

### 阶段 3：摄像头场景优化

目标是提升真实摄像头环境下的稳定性。

修改建议：

- 采集摄像头环境下的 unripe/ripe/overripe 样本。
- 重新统计 HSV 和 GLCM 特征分布。
- 调整实时模式专用阈值或加入 `camera_rules` 配置节。
- 增加背景约束提示，例如白纸背景、固定距离、均匀光照。
- 如分割不稳定，可考虑加入 ROI 裁剪、手动选择区域或背景抑制。

## 进阶版方案（SVM / Logistic）

当前基础版界面仅开放"规则分类"和"KNN"两种分类方法。SVM 和 Logistic Regression 作为进阶版方案保留在代码库中，但尚未在桌面应用界面中开放，原因如下：

1. **模型文件尚未生成**：当前数据量下 SVM/Logistic 模型文件（`svm_model.pkl`、`logistic_model.pkl`）不一定存在或泛化能力有限。
2. **基础版优先可用性**：规则分类不需要模型文件，KNN 在小样本条件下也有一定参考价值，优先确保基础版稳定可用。
3. **进阶版需要更多数据**：SVM 和 Logistic 通常需要更多训练样本才能体现优势，尤其是 RBF-kernel SVM。

后续启用进阶版的步骤：

1. 确保三类香蕉样本（unripe / ripe / overripe）每类不少于 30 张，且已按 `data/raw/<label>/` 放置。
2. 运行 `python -m src.main_rule_based --input data/raw --config config.yaml` 生成 `combined_features.csv`。
3. 运行 `python -m src.main_ml --config config.yaml` 训练 SVM 和 Logistic 模型。
4. 在 `src/app_pyqt.py` 中将 `CLASS_METHODS` 恢复为 `["规则分类", "KNN", "SVM", "Logistic"]`。
5. 重新运行 `python -m src.app_pyqt` 即可在界面中选择 SVM/Logistic。

进阶版代码（`src/ml_classifier.py` 中的 `make_svm`、`make_logistic`、模型训练和评估流程）已就绪，`METHOD_TO_MODEL` 映射也未删除，仅在界面层面暂时隐藏。

## 当前工程目录

```text
banana_ripeness_hgsk/
├── README.md
├── requirements.txt
├── config.yaml
├── AGENTS.md
├── CLAUDE.md
├── doc/
│   └── project_plan.md
├── data/
│   ├── raw/
│   │   ├── unripe/
│   │   ├── ripe/
│   │   └── overripe/
│   ├── processed/
│   │   ├── masks/
│   │   ├── cropped/
│   │   └── visualized/
│   └── features/
├── models/
├── report/
│   ├── figures/
│   ├── experiment_report.md
│   └── report.md
├── results/
│   ├── comparison/
│   ├── machine_learning/
│   └── rule_based/
├── src/
│   ├── app_pyqt.py
│   ├── dataset_builder.py
│   ├── evaluation.py
│   ├── feature_glcm.py
│   ├── feature_hsv.py
│   ├── main_ml.py
│   ├── main_rule_based.py
│   ├── ml_classifier.py
│   ├── morphology.py
│   ├── preprocessing.py
│   ├── rule_classifier.py
│   ├── segmentation.py
│   ├── utils.py
│   └── visualization.py
└── tests/
    └── test_features.py
```

## 主要模块说明

| 文件 | 功能 |
| --- | --- |
| `src/app_pyqt.py` | PyQt5 桌面应用入口，支持单图识别、批量检测和摄像头实时识别 |
| `src/inference.py` | 帧级推理封装，支持摄像头实时特征提取、香蕉候选验证和分类调度 |
| `src/dataset_builder.py` | 单张图片特征提取与特征表构建 |
| `src/main_rule_based.py` | 规则分类批处理入口，生成 CSV、mask 和可视化图片 |
| `src/main_ml.py` | 机器学习训练与评估入口，支持 KNN、SVM、Logistic |
| `src/preprocessing.py` | 图像缩放、滤波和亮度归一化 |
| `src/segmentation.py` | 基于 HSV 阈值生成香蕉候选区域 |
| `src/morphology.py` | mask 清理、最大连通区域提取、边界框计算 |
| `src/feature_hsv.py` | 提取绿色比例、黄色比例、暗色比例和 HSV 统计特征 |
| `src/feature_glcm.py` | 提取 GLCM contrast、energy、homogeneity、correlation |
| `src/rule_classifier.py` | 根据人工阈值判断成熟度类别 |
| `src/ml_classifier.py` | KNN、SVM、Logistic 模型创建、保存、加载与预测 |
| `src/evaluation.py` | 分类报告、混淆矩阵、交叉验证和模型对比 |
| `src/visualization.py` | 生成 mask 叠加图、分类标注图和横向对比图 |
| `src/utils.py` | 配置读取、路径处理、图片读写等工具函数 |
| `report/experiment_report.md` | 实验过程、数据统计、分类结果和局限性分析 |
| `report/report.md` | 工程修改记录 |

## 安装依赖

建议使用 Python 3.10 或 Python 3.11。

```bash
pip install -r requirements.txt
```

当前主要依赖包括：

- `opencv-python`
- `numpy`
- `pandas`
- `scikit-image`
- `scikit-learn`
- `matplotlib`
- `PyYAML`
- `joblib`
- `PyQt5`
- `pytest`

## 数据放置方式

将图片按真实类别放入对应目录：

```text
data/raw/unripe/
data/raw/ripe/
data/raw/overripe/
```

当前建议数据量：

- 基础展示：每类不少于 20 张。
- 机器学习训练：每类 30-50 张更合适。
- 摄像头实时优化：建议每类额外采集 20 张以上摄像头环境样本。
- 三类样本数量尽量均衡。

注意：

- 不要将真实图片数据提交到 Git 仓库。
- 不要提交生成的 CSV、图片结果、模型文件，除非用户明确需要。

## 运行现有规则分类流程

批量处理 `data/raw` 下所有图片：

```bash
python -m src.main_rule_based --input data/raw --config config.yaml
```

处理单张图片：

```bash
python -m src.main_rule_based --input path/to/banana.jpg --config config.yaml
```

只生成 CSV，不保存图片结果：

```bash
python -m src.main_rule_based --input data/raw --config config.yaml --no-save-images
```

运行后会生成：

```text
results/rule_based/summary.csv
data/features/combined_features.csv
data/processed/masks/
data/processed/visualized/
results/rule_based/images/
```

## 运行现有机器学习流程

先运行规则分类流程生成特征表：

```bash
python -m src.main_rule_based --input data/raw --config config.yaml
```

再运行机器学习训练与评估：

```bash
python -m src.main_ml --config config.yaml
```

当前如果只有单类别样本，可用于代码流程验证：

```bash
python -m src.main_ml --config config.yaml --allow-single-class
```

多类别数据补齐后，机器学习流程会输出：

- 规则分类 baseline。
- KNN/SVM/Logistic 分类报告。
- 混淆矩阵。
- 交叉验证对比结果。
- 模型文件。

## 运行现有 PyQt5 应用

启动桌面应用：

```bash
python -m src.app_pyqt
```

当前已支持：

- 打开单张图片并识别。
- 显示原图、分割 mask、识别结果图。
- 显示预测类别、食用建议和 9 项关键特征。
- **进阶版**分类方法：规则分类、KNN、SVM、Logistic。
  - **规则分类**：无需模型文件，始终可用。
  - **KNN/SVM/Logistic**：必须经过三分类训练后才可用。若模型文件缺失、类别不完整或预测异常，系统会自动检测并回退到规则分类。
  - 训练三分类模型：`python -m src.main_ml --config config.yaml`。
  - 单图和摄像头实时模式可显示 ML 概率/置信度；模型过期时状态栏会提示重新训练。
- 选择文件夹进行批量检测。
- 导出批量检测 CSV。
- **笔记本前置摄像头实时识别**：打开/关闭摄像头、暂停/继续、截图识别、镜像翻转、三栏实时显示（原图、mask、结果图）、多帧稳定性投票、非香蕉物体过滤。

## 后续进阶版优化 Agent 提示词

下面提示词可用于让 agent 继续优化已开放 ML 实时识别后的进阶版项目：

```text
你是一个严谨的 Python + OpenCV + PyQt5 工程助手。请在当前 banana_ripeness_hgsk 工程中继续优化进阶版机器学习实时识别功能。先阅读 README.md、report/report.md、config.yaml、src/app_pyqt.py、src/inference.py、src/ml_classifier.py、src/main_ml.py 和 tests/test_features.py，再动手修改。

当前背景：
1. 基础版已完成主要验收，规则分类在 75 张有效静态样本上达到 74/75 = 98.67%。
2. 进阶版第一轮已完成：UI 已开放规则分类、KNN、SVM、Logistic；单图和摄像头实时模式能显示 ML 概率/置信度；KNN/SVM/Logistic 均支持模型过期检查和规则分类回退。
3. 当前不足：批量检测表格/CSV 尚未逐条显示实际方法、置信度和三类概率；单图/截图缺少多模型并行对比；摄像头实时 ML 概率尚未做平滑；模型元数据尚未完整可视化。

开发目标：
1. 批量结果增强：
   - BatchWorker 输出 method_requested、method_used、confidence、prob_overripe、prob_ripe、prob_unripe。
   - 批量表格增加“实际方法”“置信度”列。
   - CSV 导出同步增加上述字段。
   - 模型回退时逐条显示回退后的 method_used。
2. 多模型并行对比：
   - 新增统一函数预测规则分类、KNN、SVM、Logistic 四种结果。
   - 单图或截图识别可显示四种方法的预测、概率和模型状态。
   - 某个模型缺失/过期/类别不完整时只标记该模型，不影响其他模型输出。
3. 置信度策略：
   - 在 config.yaml 增加 ml.min_confidence、ml.smooth_window、ml.show_model_comparison。
   - 摄像头实时模式对最近 smooth_window 次概率做滑动平均。
   - top-1 概率低于 min_confidence 时显示“低置信”，同时显示规则分类结果作为参考。
4. 模型元数据可视化：
   - UI 显示模型是否存在、classes、n_samples、class_counts、train_time、test_accuracy、cv_accuracy。
   - 切换分类方法时刷新模型状态。
5. 文档与报告：
   - 将进阶版优化结果写入 README.md 或 report/experiment_report.md。
   - 每次实际修改工程文件后，在 report/report.md 顶部追加修改记录。

工程约束：
1. 优先复用现有 src/inference.py、src/ml_classifier.py 和 config.yaml，不重复图像处理或特征提取逻辑。
2. 不要提交真实图片数据。
3. 不要提交生成的 CSV、图片结果、模型文件，除非用户明确要求。
4. 修改 Python 代码后运行 python -m compileall src tests。
5. 如果当前环境安装了 pytest，继续运行 python -m pytest -q。
6. 修改记录必须说明修改内容、修改原因、优化点、不足点和未完成项。

验收标准：
1. python -m src.app_pyqt 可正常启动。
2. 规则分类、KNN、SVM、Logistic 四种方法均不破坏单图、批量、截图和摄像头实时识别。
3. 批量表格和导出 CSV 包含实际方法、置信度和三类概率。
4. 单图或截图能查看多模型对比结果。
5. 模型缺失、类别不完整、过期、低置信均有明确 UI 提示并可回退。
6. report/report.md 已同步记录本次修改。
```

## 历史进阶版机器学习实时识别 Agent 提示词（已完成第一轮）

下面提示词可用于让 agent 继续开发进阶版“机器学习模型实时识别”功能：

```text
你是一个严谨的 Python + OpenCV + PyQt5 工程助手。请在当前 banana_ripeness_hgsk 工程中开发进阶版“机器学习模型实时识别”方案。先阅读 README.md、report/report.md、config.yaml、src/app_pyqt.py、src/inference.py、src/ml_classifier.py、src/main_ml.py 和 tests/test_features.py，再动手修改。

当前背景：
1. 基础版已完成主要验收目标：规则分类在更新后 75 张有效静态样本上达到 74/75 = 98.67%。
2. overripe 和 unripe 误判样本已替换并复测，召回均为 100%；仅 ripe/banana-24.jpg 是未替换的边界样本。
3. 摄像头实时识别基础链路已存在：打开/关闭/暂停/截图、候选验证、多帧投票、camera_rules、camera_preprocessing、candidate_reason、规则集显示、KNN 模型过期提示。
4. KNN/SVM/Logistic 模型已可由 python -m src.main_ml --config config.yaml 训练，并已生成模型元数据 JSON。
5. src/inference.py 和 src/app_pyqt.py 已有 METHOD_TO_MODEL 映射，当前 UI 仅通过 CLASS_METHODS = ["规则分类", "KNN"] 隐藏 SVM/Logistic。

开发目标：
1. 开放进阶版分类方法：
   - 将 PyQt5 界面分类方法扩展为：规则分类、KNN、SVM、Logistic。
   - 不删除规则分类兜底。
   - 保持单图、批量、截图、摄像头实时四条路径都能处理模型缺失、模型类别不完整和预测异常。
2. 增强实时机器学习结果显示：
   - 显示实际使用的方法 method_used。
   - 显示 top-1 概率或置信度。
   - 显示 KNN/SVM/Logistic 的概率分布；概率不可用时明确显示“概率不可用”。
   - 当 ML 低置信或回退到规则分类时，在 UI 中明确标注“低置信/已回退”。
3. 增强模型状态管理：
   - 将现有 KNN 过期检查扩展为通用模型状态检查，支持 KNN/SVM/Logistic。
   - 读取 *_model_meta.json，显示模型类别、训练样本数、训练时间、test accuracy、CV accuracy。
   - 如果 combined_features.csv 比模型元数据更新，提示运行 python -m src.main_ml --config config.yaml 重新训练。
4. 增加模型对比输出：
   - 单图或截图识别可显示规则分类、KNN、SVM、Logistic 的对比结果。
   - 批量检测可增加不同模型预测列，便于导出 CSV 后分析。
   - 在 report/experiment_report.md 或 README.md 中记录进阶版模型对比结论。

工程约束：
1. 优先复用现有 src/inference.py、src/ml_classifier.py 和 config.yaml，不要复制图像处理或特征提取逻辑。
2. 不要提交真实图片数据。
3. 不要提交生成的 CSV、图片结果、模型文件，除非用户明确要求。
4. 修改 Python 代码后运行 python -m compileall src tests。
5. 如果当前环境安装了 pytest，继续运行 python -m pytest -q。
6. 每次实际修改工程文件后，必须在 report/report.md 顶部追加修改记录，包含修改时间、文件列表、具体位置、优化点、不足点和未完成项。

验收标准：
1. python -m src.app_pyqt 可正常启动。
2. UI 中可选择规则分类、KNN、SVM、Logistic。
3. 模型文件缺失、类别不完整或过期时有明确提示并回退，不崩溃。
4. 摄像头实时模式下 ML 模型不会每帧重复加载，仍使用模型缓存。
5. 识别结果能显示概率/置信度/实际方法/回退原因。
6. 单图、批量、截图和摄像头实时识别均不破坏基础版功能。
7. report/report.md 已同步记录本次修改。
```

## 历史基础版剩余优化 Agent 提示词（已完成主要验收）

下面提示词可用于让 agent 基于最新样本替换情况继续优化基础版项目：

```text
你是一个严谨的 Python + OpenCV + PyQt5 工程助手。请在当前 banana_ripeness_hgsk 工程中继续优化基础版“香蕉成熟度实时识别应用系统”。先阅读 README.md、report/report.md、config.yaml、src/inference.py、src/app_pyqt.py、src/rule_classifier.py、src/ml_classifier.py 和 tests/test_features.py，再动手修改。

当前背景：
1. data/raw/overripe/ 已新增 10 张过熟香蕉图片，用于替代上一轮效果不理想的网络图片。
2. data/raw/unripe/ 已新增 7 张未成熟香蕉图片，用于替代上一轮效果不理想的网络图片。
3. 当前三类样本目录数量保持平衡，但新样本会改变 HSV/GLCM 特征分布，必须重新复测规则分类和 KNN 模型。
4. 摄像头实时识别基础链路已存在：src/inference.py + src/app_pyqt.py，包含 camera_preprocessing、camera_rules、candidate 候选验证和 stability 多帧投票。
5. 当前主要问题是：实时识别准确率偏低、复杂背景/人/物体干扰导致无法检测或误检、环境光导致成熟度误判。

工作目标：
1. 不重构无关代码，优先复用现有模块和 config.yaml 参数。
2. 先完成最新静态样本复测：
   - 运行 python -m src.main_rule_based --input data/raw --config config.yaml。
   - 统计三类准确率、召回率、混淆矩阵和失败样本。
   - 运行 python -m src.main_ml --config config.yaml 重新训练 KNN/SVM/Logistic；基础版 UI 仍只开放规则分类和 KNN。
3. 再优化摄像头基础版鲁棒性：
   - 不要把阈值硬编码到 Python 文件，优先调整 config.yaml 中 candidate、camera_rules、camera_preprocessing、stability。
   - candidate 优先解决“非香蕉物体/人/背景误检”和“无法识别到香蕉”。
   - camera_rules 和 camera_preprocessing 优先解决“光照变化导致成熟度误判”。
   - stability 优先解决“实时结果跳变”和“短暂遮挡”。
4. 增强界面可解释性：
   - 摄像头模式显示 candidate_reason。
   - 显示当前使用的规则集名称：静态 rules 或 camera_rules。
   - 区分“未检测到香蕉”和“检测到香蕉但成熟度低置信/回退分类”。
   - KNN 加载时尽量读取模型元数据；若 combined_features.csv 比模型训练时间更新，提示重新训练。

工程约束：
1. 不要提交真实图片数据。
2. 不要提交生成的 CSV、图片结果、模型文件，除非用户明确要求。
3. 修改 Python 代码后至少运行 python -m compileall src tests。
4. 如果当前环境安装了 pytest，继续运行 python -m pytest -q。
5. 每次实际修改工程文件后，必须在 report/report.md 顶部追加修改记录，包含修改时间、文件列表、具体位置、优化点、不足点和未完成项。

验收标准：
1. 单图识别、批量检测、摄像头实时识别均能继续启动，不破坏已有功能。
2. 最新样本替换后的规则分类和 KNN 复测结果有明确记录。
3. 摄像头模式对非香蕉物体、人、复杂背景、强光/暗光的失败原因更明确。
4. 参数优化集中在 config.yaml，Python 代码只做必要的流程和 UI 可解释性增强。
5. report/report.md 已同步记录本次修改。
```

## 历史实时识别开发 Agent 提示词（已完成基础链路）

下面提示词是早期用于从零开发摄像头实时识别基础链路的历史版本，当前仅作为方案演进记录保留：

```text
你是一个严谨的 Python + OpenCV + PyQt5 工程助手。请在当前 banana_ripeness_hgsk 工程中继续开发“基于 OpenCV 与机器学习的香蕉成熟度实时识别应用系统”，在现有 PyQt5 单图识别和批量检测基础上，新增笔记本电脑前置摄像头实时识别功能。不要重构无关代码，不要删除已有功能。

当前项目现状：
1. 已有 OpenCV 图像处理与特征提取模块：
   - src/preprocessing.py
   - src/segmentation.py
   - src/morphology.py
   - src/feature_hsv.py
   - src/feature_glcm.py
   - src/dataset_builder.py
   - src/visualization.py
2. 已有规则分类与机器学习模块：
   - src/rule_classifier.py
   - src/ml_classifier.py
   - src/main_rule_based.py
   - src/main_ml.py
   - src/evaluation.py
3. 已有 PyQt5 桌面应用入口：
   - src/app_pyqt.py
   - 当前已支持单张图片识别、批量检测、CSV 导出和模型选择。

开发目标：
1. 新增帧级推理封装，建议新建 src/inference.py：
   - extract_features_for_frame(frame_bgr, config)
   - predict_features(features, config, method, model_cache)
   - run_inference_on_frame(frame_bgr, config, method, model_cache)
2. 在 src/app_pyqt.py 中新增摄像头实时识别功能：
   - 打开笔记本前置摄像头，默认使用 cv2.VideoCapture(0)；
   - 支持关闭摄像头并释放资源；
   - 支持暂停/继续实时画面；
   - 支持截图识别；
   - 实时显示摄像头原始画面、分割 mask 和识别结果图；
   - 显示预测类别、食用建议和 green_ratio、yellow_ratio、dark_ratio、H_mean、S_mean、V_mean、glcm_contrast、glcm_energy、glcm_homogeneity 等关键特征。
3. 摄像头模式默认先使用规则分类器，确保无模型文件也能运行。
4. 当选择 KNN/SVM/Logistic 但模型文件不存在时，界面应明确提示并允许回退到规则分类，不要崩溃。
5. 实时性能要求：
   - 摄像头画面刷新和推理计算分开控制；
   - 推理间隔建议 500 ms；
   - 实时推理最长边建议缩放到 640；
   - ML 模型应缓存，不要每帧重复加载；
   - 使用 QThread 或 QTimer 避免 UI 卡死。
6. 建议在 config.yaml 新增 camera 配置：
   camera:
     device_index: 0
     width: 1280
     height: 720
     display_fps: 30
     inference_interval_ms: 500
     realtime_max_size: 640
     mirror: false

界面建议：
1. 顶部工具区增加：
   - 打开摄像头按钮；
   - 关闭摄像头按钮；
   - 暂停/继续按钮；
   - 截图识别按钮；
   - 摄像头编号选择；
   - 分类方法选择。
2. 中部图像区复用现有三栏布局：
   - 左侧显示摄像头原始帧；
   - 中间显示分割 mask；
   - 右侧显示识别结果图。
3. 底部信息区复用现有预测类别、食用建议和特征值表格。

工程约束：
1. 优先复用现有 src/ 模块，不要复制已有算法逻辑。
2. 不要提交真实图片数据。
3. 不要提交生成的 CSV、图片结果、模型文件，除非用户明确要求。
4. 修改 Python 代码后运行：
   python -m compileall src tests
5. 如果当前环境安装了 pytest，继续运行：
   python -m pytest -q
6. 每次修改工程文件后，必须在 report/report.md 顶部追加本次修改记录。

验收标准：
1. 可以通过 python -m src.app_pyqt 启动桌面应用。
2. 点击“打开摄像头”后能显示笔记本前置摄像头画面。
3. 将香蕉放到摄像头前时，界面能显示原始帧、mask、结果图、预测类别和特征值。
4. 点击“关闭摄像头”后摄像头资源被释放。
5. 模型文件不存在或预测异常时有友好提示并可回退到规则分类。
6. 不破坏现有单图识别、批量检测、main_rule_based.py 和 main_ml.py 命令行流程。
```

## 测试

修改 Python 代码后至少运行：

```bash
python -m compileall src tests
```

如果当前环境安装了 `pytest`，继续运行：

```bash
python -m pytest -q
```

仅修改 Markdown 文档时，不强制运行上述命令。

## 修改记录规范

`report/report.md` 的定位是工程修改记录，不是最终实验报告。每次修改工程文件后，应在该文件顶部追加一条修改记录，记录内容包括：

- 本次内容修改完成时间。
- 本次修改的文件列表和具体修改位置。
- 本次修改后项目相对于上一版项目的优化点。
- 本次修改后仍存在的不足点。
- 本次修改未完成或需要继续优化的部分。

仓库根目录提供：

- `AGENTS.md`：供 Codex 等支持仓库级指令文件的 agent 读取。
- `CLAUDE.md`：供 Claude Code 读取。

## 项目历史：PyQt5 图片识别与批量检测方案

上一版项目题目为：

> 基于 OpenCV 与机器学习的香蕉成熟度识别应用系统

上一版推荐英文题目为：

> Banana Ripeness Recognition Application System Based on OpenCV and Machine Learning

上一版推荐缩写：

> BRR-OML

上一版方案将项目从命令行算法流水线升级为 PyQt5 桌面应用，重点是“单张图片上传识别 + 批量图片检测 + CSV 导出”。该方案的系统架构为：

```text
PyQt5 桌面应用界面
  -> 图片选择 / 文件夹选择
  -> OpenCV 图像预处理
  -> 香蕉主体区域分割
  -> HSV + GLCM 特征提取
  -> 规则分类器 / KNN / SVM / Logistic 预测
  -> 原图 + mask + 结果图 + 特征表 + 预测结果展示
  -> 批量检测结果导出
```

上一版应用界面功能设计：

- “打开图片”按钮。
- “选择文件夹”按钮。
- “分类方法”下拉框：规则分类、KNN、SVM、Logistic。
- “开始识别”按钮。
- “导出 CSV”按钮。
- 原图显示区域。
- 分割 mask 显示区域。
- 识别结果图显示区域。
- 成熟度类别显示区域。
- 食用建议显示区域。
- 特征值表格。
- 批量检测结果表格。

上一版单图流程：

```text
选择图片
-> 读取图片
-> 预处理
-> 分割香蕉主体
-> 提取 HSV 与 GLCM 特征
-> 根据界面选择调用规则分类器或 ML 模型
-> 显示原图、mask、结果图、类别、特征值
```

上一版批量流程：

```text
选择图片文件夹
-> 遍历图片
-> 批量提取特征
-> 批量预测成熟度
-> 表格展示 image_path、prediction、主要特征值
-> 导出 CSV
```

上一版方案的优点：

- 已经形成可操作的桌面应用入口。
- 复用现有算法模块，没有复制图像处理逻辑。
- 单图识别和批量检测适合课程展示。
- 模型文件缺失时有友好提示和规则分类回退。

上一版方案的不足：

- 输入仍以静态图片为主，实时交互性不足。
- 无法直接展示“拿起香蕉对准摄像头即可识别”的应用效果。
- 批量检测偏离现场演示场景。
- 摄像头采集场景下的光照和背景鲁棒性尚未验证。

因此，当前方案在上一版 PyQt5 应用基础上增加“笔记本电脑前置摄像头实时识别”，使系统更接近完整应用展示。

## 项目历史：原始两阶段算法方案

本项目最初题目为：

> 基于 HSV 颜色比例与 GLCM 纹理特征的香蕉成熟度识别

原始方案采用“两阶段递进式”实现。

第一阶段：基础版规则分类。

```text
图像输入
-> 图像预处理
-> HSV 颜色空间转换
-> 香蕉区域分割
-> 形态学处理
-> 最大连通区域提取
-> HSV 颜色比例特征提取
-> GLCM 纹理特征提取
-> 人工规则分类
-> 输出 CSV 与可视化结果
```

第二阶段：进阶版机器学习分类。

```text
图像输入
-> 图像预处理
-> 香蕉区域分割
-> HSV + GLCM 特征提取
-> 构建特征向量
-> 保存特征 CSV
-> 数据集划分
-> 特征归一化
-> 训练 KNN/SVM 分类器
-> 测试集预测
-> 模型评估
-> 输出实验结果
```

原始方案的优点：

- 技术路线清晰，适合课程中的数字图像处理实验。
- 基础版可以独立运行并生成中间结果。
- 进阶版可以自然复用基础版特征。
- 规则分类、KNN、SVM 可以形成对比实验。

原始方案的不足：

- 最终呈现偏命令行和实验报告，不是完整应用系统。
- 缺少用户交互界面。
- 缺少单图上传、模型选择、结果解释、批量检测和摄像头实时识别等应用功能。

因此，项目先升级为 PyQt5 图片识别应用系统，再进一步升级为支持笔记本前置摄像头的实时识别应用系统。
