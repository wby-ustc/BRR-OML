# 基于 HSV 颜色比例与 GLCM 纹理特征的香蕉成熟度识别

本工程用于实现香蕉成熟度识别的基础版流程。当前版本采用传统数字图像处理方法，不依赖机器学习训练即可完成图片读取、香蕉主体区域分割、HSV 颜色比例特征提取、GLCM 纹理特征提取、人工规则分类和结果可视化。

项目分类目标为三类：

- `unripe`：未成熟，表面以绿色或黄绿色为主。
- `ripe`：成熟，表面以黄色为主，黑斑较少。
- `overripe`：过熟，表面存在明显黑斑、褐色区域或整体颜色变暗。

## 当前工程内容

当前工程已经完成基础版代码框架，主要包括：

- 工程目录初始化。
- 原始数据、处理结果、特征文件、模型文件、报告文件目录划分。
- 图像预处理模块。
- HSV 颜色空间分割模块。
- 形态学处理与最大连通区域提取模块。
- HSV 颜色比例特征提取模块。
- GLCM 纹理特征提取模块。
- 基于人工阈值的规则分类模块。
- 分割 mask、预测结果图和对比图生成模块。
- 批量处理入口 `src/main_rule_based.py`。
- 机器学习扩展入口 `src/main_ml.py` 的基础骨架。
- 简单测试文件 `tests/test_features.py`。

## 工程目录说明

```text
banana_ripeness_hgsk/
├── README.md
├── requirements.txt
├── config.yaml
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
│   │   └── images/
│   ├── machine_learning/
│   │   └── images/
│   └── comparison/
├── report/
│   ├── figures/
│   └── report.md
└── tests/
    └── test_features.py
```

## 核心流程

基础版处理流程如下：

```text
图像输入
→ 图像预处理
→ HSV 颜色空间转换
→ 香蕉候选区域分割
→ 形态学开闭运算
→ 最大连通区域提取
→ HSV 颜色比例特征提取
→ GLCM 纹理特征提取
→ 人工阈值规则分类
→ 输出 CSV 与可视化结果
```

## 主要模块说明

| 文件 | 功能 |
| --- | --- |
| `src/main_rule_based.py` | 基础版主程序，批量处理图片并输出结果 |
| `src/preprocessing.py` | 图像缩放、滤波和亮度归一化 |
| `src/segmentation.py` | 基于 HSV 阈值生成香蕉候选区域 |
| `src/morphology.py` | mask 清理、最大连通区域提取、边界框计算 |
| `src/feature_hsv.py` | 提取绿色比例、黄色比例、暗色比例和 HSV 均值标准差 |
| `src/feature_glcm.py` | 提取 GLCM contrast、energy、homogeneity、correlation |
| `src/rule_classifier.py` | 根据人工阈值判断成熟度类别 |
| `src/visualization.py` | 生成 mask 叠加图和分类结果图 |
| `src/dataset_builder.py` | 单张图片特征提取与特征表构建 |
| `src/main_ml.py` | 后续 SVM/KNN 机器学习版本入口 |
| `config.yaml` | 路径、预处理参数、分割参数和分类阈值配置 |
| `report/report.md` | 项目修改记录，按时间倒序记录每次工程修改的文件、优化点、不足点和待办事项 |
| `AGENTS.md` | Codex 等 agent 的仓库级默认工作规则 |
| `CLAUDE.md` | Claude Code 的仓库级默认工作规则 |

## 安装依赖

建议使用 Python 3.10 或 Python 3.11。

```bash
pip install -r requirements.txt
```

主要依赖包括：

- `opencv-python`
- `numpy`
- `pandas`
- `scikit-image`
- `scikit-learn`
- `matplotlib`
- `PyYAML`
- `joblib`
- `pytest`

## 数据放置方式

将图片按真实类别放入对应目录：

```text
data/raw/unripe/
data/raw/ripe/
data/raw/overripe/
```

如果只是测试单张图片，也可以直接指定图片路径运行。目录名会被程序用于推断真实标签，便于后续生成对比结果。

## 运行基础版

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

## 输出结果

运行完成后会生成：

```text
results/rule_based/summary.csv
data/features/combined_features.csv
data/processed/masks/
data/processed/visualized/
results/rule_based/images/
```

其中：

- `summary.csv` 保存每张图片的真实标签、HSV 特征、GLCM 特征、规则分类结果和 mask 面积。
- `combined_features.csv` 保存后续机器学习版本可复用的特征表。
- `masks/` 保存香蕉主体区域二值 mask。
- `visualized/` 保存带分类结果的可视化图片。
- `results/rule_based/images/` 保存原图、mask、结果图的横向对比图。

## 参数配置

主要参数位于 `config.yaml`：

```yaml
preprocessing:
  max_size: 900
  blur_kernel: 5

segmentation:
  min_area_ratio: 0.01
  morphology_kernel: 7

features:
  glcm_levels: 32
  glcm_distances: [1, 2]

rules:
  green_ratio_threshold: 0.32
  dark_ratio_threshold: 0.18
  contrast_threshold: 35.0
  yellow_ratio_threshold: 0.45
```

阈值需要结合实际拍摄数据调整。建议先检查 `data/processed/masks/` 中的分割效果，再根据 `summary.csv` 中的特征统计修改规则阈值。

## 当前基础版状态

当前基础版已经具备完整运行链路，但仍属于初始可运行版本。它适合用于：

- 课程项目的基础功能展示。
- 收集样本后的初步实验。
- 观察 HSV 颜色比例与成熟度之间的关系。
- 生成后续机器学习分类所需的特征 CSV。

当前版本的主要限制：

- HSV 阈值对光照、背景颜色和拍摄角度较敏感。
- 人工规则阈值需要根据实际样本调整。
- 香蕉区域分割在复杂背景下可能失败。
- GLCM 纹理特征目前基于主体区域边界框计算，仍可进一步优化。
- 机器学习版本已有入口和模块骨架，但需要在采集足够样本后继续完善训练、评估和对比实验。

## 修改记录规范

`report/report.md` 的定位是工程修改记录，不是最终实验报告。每次修改工程文件后，应在该文件顶部追加一条修改记录，记录内容包括：

- 本次内容修改完成时间。
- 本次修改的文件列表和具体修改位置。
- 本次修改后项目相对于上一版项目的优化点。
- 本次修改后仍存在的不足点。
- 本次修改未完成或需要继续优化的部分。

为了避免每次对话重复说明该要求，仓库根目录提供了：

- `AGENTS.md`：供 Codex 等支持仓库级指令文件的 agent 读取。
- `CLAUDE.md`：供 Claude Code 读取。

其他 AI agent 工具如果支持项目级规则文件，应将同样规则复制到其默认读取的项目说明文件中，或在工具配置中指向 `AGENTS.md`。

## 测试

运行语法检查：

```bash
python -m compileall src tests
```

安装 `pytest` 后运行单元测试：

```bash
python -m pytest -q
```

## 基础版后续步骤 Agent 提示词

```text
你是一个严谨的 Python 图像处理工程助手。请在当前 banana_ripeness_hgsk 工程基础上继续完善基础版香蕉成熟度识别系统，不要重构无关代码，不要删除已有功能。

目标：
1. 基于当前 src/main_rule_based.py、segmentation.py、feature_hsv.py、feature_glcm.py、rule_classifier.py 等模块，提升基础版规则分类效果。
2. 重点完善图像分割、特征统计、阈值调试、结果分析和报告材料，而不是直接进入深度学习。

具体任务：
1. 检查 data/raw/unripe、data/raw/ripe、data/raw/overripe 中的样本数量和图片格式，给出数据集概况。
2. 运行基础版流程，生成 results/rule_based/summary.csv、data/features/combined_features.csv、mask 图和可视化结果图。
3. 根据 summary.csv 统计每一类样本的 green_ratio、yellow_ratio、dark_ratio、glcm_contrast、glcm_homogeneity 等特征分布。
4. 检查分割失败或 mask 面积异常的样本，记录文件名和可能原因。
5. 根据真实标签与 rule_prediction 的对比，计算基础版规则分类准确率，并列出错误分类样本。
6. 基于统计结果调整 config.yaml 中的规则阈值，例如 green_ratio_threshold、dark_ratio_threshold、contrast_threshold、yellow_ratio_threshold。
7. 重新运行基础版流程，比较调整前后的准确率和错误样本变化。
8. 将实验分析整理到单独的实验报告文件，例如 report/experiment_report.md，包括数据集数量、处理流程、关键特征解释、阈值设置、分类结果、失败案例和改进方向。
9. 按 report/report.md 的修改记录模板，在 report/report.md 顶部追加本次工程修改记录。
10. 如有必要，增加少量测试用例，确保 HSV 特征提取、GLCM 特征提取和规则分类函数行为稳定。

约束：
- 保持当前工程结构不变。
- 不要提交真实图片数据到 Git 仓库。
- 不要把生成的 CSV、图片结果、模型文件提交到 Git 仓库，除非用户明确要求。
- 优先使用现有模块和 config.yaml 参数，不要引入复杂新框架。
- 所有代码修改后需要至少运行 python -m compileall src tests。
- 如果 pytest 可用，运行 python -m pytest -q。

最终输出：
1. 说明修改了哪些文件。
2. 给出基础版当前准确率和主要错误样本。
3. 说明阈值调整依据。
4. 给出后续进入 SVM/KNN 机器学习版本前还需要补充的数据和实验。
```
