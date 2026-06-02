# 基于 OpenCV 与机器学习的香蕉成熟度识别应用系统

本项目面向香蕉成熟度识别的课程/实验应用开发，目标是从“图像处理算法流水线”升级为一个可交互的桌面应用系统。系统以自己采集的香蕉图片为输入，使用 OpenCV 完成图像预处理、香蕉主体分割、颜色与纹理特征提取，并结合规则分类器和机器学习模型判断香蕉成熟度。

当前项目题目：

> 基于 OpenCV 与机器学习的香蕉成熟度识别应用系统

推荐英文题目：

> Banana Ripeness Recognition Application System Based on OpenCV and Machine Learning

推荐缩写：

> BRR-OML

## 项目目标

本项目最终应以“应用系统”的形式展示，而不是只运行若干数字图像处理算法。最终系统建议包含：

- 图形化界面，推荐使用 PyQt5。
- 单张图片上传与识别。
- 原图、分割 mask、识别结果图同步展示。
- HSV 颜色比例与 GLCM 纹理特征展示。
- 规则分类与机器学习分类结果展示。
- 批量图片检测与 CSV 导出。
- 分类准确率、混淆矩阵和实验报告展示。

成熟度类别设计为三类：

- `unripe`：未成熟，表面以绿色或黄绿色为主。
- `ripe`：成熟，表面以黄色为主，黑斑较少。
- `overripe`：过熟，表面存在明显黑斑、褐色区域或整体颜色变暗。

## 当前代码状态

当前工程已经具备算法层的主要能力：

- OpenCV 图像读取、缩放、滤波和亮度归一化。
- HSV 颜色空间分割。
- 形态学开闭运算与最大连通区域提取。
- HSV 颜色比例特征提取。
- GLCM 纹理特征提取。
- 基于人工阈值的规则分类器。
- KNN、SVM、Logistic Regression 机器学习分类器代码。
- 分类报告、混淆矩阵、交叉验证和模型对比代码。
- mask、标注图、对比图、CSV 结果输出。
- 基础测试用例。

当前工程尚未完成应用层：

- 尚未提供 PyQt5 桌面界面。
- 尚未提供单图上传、模型选择、结果可视化的交互入口。
- 当前数据集中只有 `ripe` 类别真实图片，`unripe` 和 `overripe` 类别样本仍需补充。
- 当前机器学习模型在数据不足时只能验证代码流程，不能代表真实三分类效果。

## 推荐最终系统架构

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

建议将现有算法模块继续保留在 `src/` 下，将应用界面新增为独立入口，例如：

```text
src/app_pyqt.py
```

或进一步拆分为：

```text
app/
├── main_window.py
├── controller.py
└── widgets.py
```

为了降低改动风险，推荐第一版先新增 `src/app_pyqt.py`，直接复用现有 `src/dataset_builder.py`、`src/visualization.py`、`src/rule_classifier.py` 和 `src/ml_classifier.py`。

## 应用界面功能设计

### 1. 单张图片识别

界面控件建议：

- “打开图片”按钮。
- “开始识别”按钮。
- “分类方法”下拉框：规则分类、KNN、SVM、Logistic。
- 原图显示区域。
- 分割 mask 显示区域。
- 识别结果图显示区域。
- 成熟度类别显示区域。
- 食用建议显示区域。
- 特征值表格。

单图流程：

```text
选择图片
-> 读取图片
-> 预处理
-> 分割香蕉主体
-> 提取 HSV 与 GLCM 特征
-> 根据界面选择调用规则分类器或 ML 模型
-> 显示原图、mask、结果图、类别、特征值
```

### 2. 批量图片检测

界面控件建议：

- “选择文件夹”按钮。
- “批量检测”按钮。
- 检测结果表格。
- “导出 CSV”按钮。

批量流程：

```text
选择图片文件夹
-> 遍历图片
-> 批量提取特征
-> 批量预测成熟度
-> 表格展示 image_path、prediction、主要特征值
-> 导出 CSV
```

### 3. 实验结果展示

可选扩展：

- 显示规则分类准确率。
- 显示 KNN/SVM/Logistic 分类报告。
- 显示混淆矩阵图片。
- 显示不同模型对比结果。

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
├── src/
│   ├── main_rule_based.py
│   ├── main_ml.py
│   ├── preprocessing.py
│   ├── segmentation.py
│   ├── morphology.py
│   ├── feature_hsv.py
│   ├── feature_glcm.py
│   ├── rule_classifier.py
│   ├── dataset_builder.py
│   ├── ml_classifier.py
│   ├── evaluation.py
│   ├── visualization.py
│   └── utils.py
├── models/
├── results/
│   ├── rule_based/
│   ├── machine_learning/
│   └── comparison/
├── report/
│   ├── figures/
│   ├── experiment_report.md
│   └── report.md
└── tests/
    └── test_features.py
```

## 主要模块说明

| 文件 | 功能 |
| --- | --- |
| `src/main_rule_based.py` | 规则分类批处理入口，生成 CSV、mask 和可视化图片 |
| `src/main_ml.py` | 机器学习训练与评估入口，支持 KNN、SVM、Logistic |
| `src/preprocessing.py` | 图像缩放、滤波和亮度归一化 |
| `src/segmentation.py` | 基于 HSV 阈值生成香蕉候选区域 |
| `src/morphology.py` | mask 清理、最大连通区域提取、边界框计算 |
| `src/feature_hsv.py` | 提取绿色比例、黄色比例、暗色比例和 HSV 统计特征 |
| `src/feature_glcm.py` | 提取 GLCM contrast、energy、homogeneity、correlation |
| `src/rule_classifier.py` | 根据人工阈值判断成熟度类别 |
| `src/dataset_builder.py` | 单张图片特征提取与特征表构建 |
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
- `pytest`

若开发 PyQt5 桌面应用，需要增加：

```bash
pip install PyQt5
```

也可以将下面依赖加入 `requirements.txt`：

```text
PyQt5>=5.15.0
```

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
- 三类样本数量尽量均衡。

注意：

- 不要将真实图片数据提交到 Git 仓库。
- 不要提交生成的 CSV、图片结果、模型文件，除非明确需要。

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

## PyQt5 应用开发建议

新增应用入口建议命名为：

```text
src/app_pyqt.py
```

第一版应用建议只实现单图识别：

```text
打开图片
-> 显示原图
-> 点击开始识别
-> 显示 mask
-> 显示标注结果图
-> 显示预测类别和特征值
```

第二版再增加：

```text
模型选择
-> 规则分类 / KNN / SVM / Logistic
-> 加载 models/*.pkl
-> 使用当前图片特征进行预测
```

第三版再增加：

```text
批量检测
-> 文件夹选择
-> 表格展示
-> CSV 导出
```

## 应用开发 Agent 提示词

下面提示词可用于让 agent 继续开发 PyQt5 应用界面和相关功能代码：

```text
你是一个严谨的 Python + OpenCV + PyQt5 工程助手。请在当前 banana_ripeness_hgsk 工程中继续开发“基于 OpenCV 与机器学习的香蕉成熟度识别应用系统”，不要重构无关代码，不要删除已有功能。

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
3. 当前目标不是只运行命令行脚本，而是补充 PyQt5 桌面应用界面。

开发目标：
1. 新增 PyQt5 应用入口 src/app_pyqt.py。
2. 实现单张图片识别功能：
   - 打开图片；
   - 显示原图；
   - 调用现有 extract_features_for_image() 或等价流程提取特征；
   - 显示香蕉分割 mask；
   - 显示带成熟度文字标注的结果图；
   - 显示预测类别；
   - 显示 green_ratio、yellow_ratio、dark_ratio、H_mean、S_mean、V_mean、glcm_contrast、glcm_energy、glcm_homogeneity 等关键特征。
3. 界面中提供分类方法选择：
   - 规则分类；
   - KNN；
   - SVM；
   - Logistic。
4. 当选择机器学习模型但模型文件不存在时，界面应给出明确提示，不要崩溃。
5. 支持批量检测作为第二阶段功能：
   - 选择文件夹；
   - 遍历图片；
   - 批量预测；
   - 表格展示图片路径、预测类别和关键特征；
   - 支持导出 CSV。

界面建议：
1. 主窗口标题：基于 OpenCV 与机器学习的香蕉成熟度识别应用系统。
2. 顶部工具区：
   - 打开图片按钮；
   - 选择文件夹按钮；
   - 分类方法下拉框；
   - 开始识别按钮；
   - 导出结果按钮。
3. 中部图像区：
   - 左侧显示原图；
   - 中间显示分割 mask；
   - 右侧显示识别结果图。
4. 底部信息区：
   - 显示预测类别；
   - 显示食用建议；
   - 使用表格展示特征值；
   - 批量模式下显示检测结果表格。

工程约束：
1. 优先复用现有 src/ 模块，不要复制已有算法逻辑。
2. 不要提交真实图片数据。
3. 不要提交生成的 CSV、图片结果、模型文件，除非用户明确要求。
4. 如需新增依赖，将 PyQt5>=5.15.0 加入 requirements.txt。
5. 修改 Python 代码后运行：
   python -m compileall src tests
6. 如果当前环境安装了 pytest，继续运行：
   python -m pytest -q
7. 每次修改工程文件后，必须在 report/report.md 顶部追加本次修改记录。

验收标准：
1. 可以通过 python -m src.app_pyqt 启动桌面应用。
2. 可以选择单张香蕉图片并完成识别。
3. 界面能显示原图、mask、结果图、预测类别和特征值。
4. 模型文件不存在或数据不足时有友好提示。
5. 不破坏现有 main_rule_based.py 和 main_ml.py 命令行流程。
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

本次 README 题目调整和文档重写不涉及 Python 代码修改，因此不强制运行上述命令。

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

## 项目历史：原始两阶段方案

本项目最初题目为：

> 基于 HSV 颜色比例与 GLCM 纹理特征的香蕉成熟度识别

原始方案采用“两阶段递进式”实现：

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
- 缺少单图上传、模型选择、结果解释、批量检测等应用功能。

因此，项目题目正式调整为“基于 OpenCV 与机器学习的香蕉成熟度识别应用系统”。新方案保留原有图像处理和机器学习算法层，将 PyQt5 桌面界面作为新的应用层目标，使项目最终能够以可操作的软件系统形式展示。
