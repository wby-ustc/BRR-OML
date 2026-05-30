# 基于 HSV 颜色比例 + GLCM 纹理特征 + SVM/KNN 分类的香蕉成熟度识别项目方案

## 1. 项目基本信息

中文题目：基于 HSV 颜色比例 + GLCM 纹理特征 + SVM/KNN 分类的香蕉成熟度识别

英文题目：Banana Ripeness Recognition Based on HSV Color Ratios and GLCM Texture Features with SVM/KNN

推荐英文缩写：BRR-HGSK

推荐工程目录名：banana_ripeness_hgsk

## 2. 项目总体思路

本项目以自己拍摄的香蕉图像为研究对象，利用数字图像处理方法提取香蕉区域的颜色特征和纹理特征，并判断香蕉成熟度。

项目采用“两阶段递进式”实现：

第一阶段：基础版  
基于 HSV 颜色比例和 GLCM 纹理特征，使用人工规则进行成熟度分类。

第二阶段：进阶版  
在基础版已经完成的图像处理和特征提取模块基础上，加入 SVM/KNN 分类器，实现机器学习分类。

两个阶段不是独立项目，而是前后衔接的同一套系统。基础版负责跑通完整图像处理流程，进阶版复用基础版的特征提取结果，在此基础上增加模型训练、预测与评估。

## 3. 成熟度类别设计

建议将香蕉成熟度分为三类：

1. 未成熟 unripe：表面以绿色或黄绿色为主。
2. 成熟 ripe：表面以黄色为主，黑斑较少。
3. 过熟 overripe：表面有明显黑斑、褐色区域或颜色变暗。

## 4. 第一阶段：基础版规则分类方案

### 4.1 阶段目标

基础版的目标是使用传统数字图像处理方法完成香蕉成熟度识别，不使用机器学习模型。

主要目标包括：

- 完成图像读取与预处理
- 完成香蕉主体区域分割
- 完成 HSV 颜色比例统计
- 完成 GLCM 纹理特征提取
- 设计人工分类规则
- 输出分类结果和中间处理图

### 4.2 基础版技术路线

图像输入  
→ 图像预处理  
→ HSV 颜色空间转换  
→ 香蕉区域分割  
→ 形态学处理  
→ 最大连通区域提取  
→ HSV 颜色比例特征提取  
→ GLCM 纹理特征提取  
→ 人工规则分类  
→ 输出识别结果

### 4.3 数据采集建议

建议自己拍摄 60 张左右香蕉图片：

- 未成熟：20 张
- 成熟：20 张
- 过熟：20 张

拍摄建议：

- 尽量使用自己拍摄的图片，符合课程要求。
- 初期背景尽量简单，便于分割。
- 后续可加入不同光照、不同角度、不同背景图片，用于分析鲁棒性。
- 每张图片应人工标注真实类别。

### 4.4 图像预处理

预处理内容包括：

- 图像尺寸统一
- 高斯滤波或中值滤波去噪
- 亮度归一化
- 可选：直方图均衡化或 Gamma 校正

预处理目标是减弱噪声和光照变化对后续颜色分割的影响。

### 4.5 香蕉区域分割

推荐使用 HSV 颜色空间进行香蕉主体分割。

基本步骤：

1. 将 BGR/RGB 图像转换为 HSV 图像。
2. 根据 H、S、V 阈值提取绿色、黄色、褐色区域。
3. 合并多个颜色区域，得到香蕉候选 mask。
4. 使用形态学开运算去除小噪声。
5. 使用形态学闭运算填补香蕉区域内部空洞。
6. 提取最大连通区域作为香蕉主体区域。

### 4.6 HSV 颜色比例特征

在香蕉 mask 内统计颜色比例和颜色分布。

推荐特征：

- green_ratio：绿色区域比例
- yellow_ratio：黄色区域比例
- dark_ratio：黑斑/褐色区域比例
- H_mean：H 通道均值
- H_std：H 通道标准差
- S_mean：S 通道均值
- S_std：S 通道标准差
- V_mean：V 通道均值
- V_std：V 通道标准差

颜色判断依据：

- green_ratio 较高，通常表示未成熟。
- yellow_ratio 较高且 dark_ratio 较低，通常表示成熟。
- dark_ratio 较高，通常表示过熟。

### 4.7 GLCM 纹理特征

将香蕉区域转换为灰度图，在 mask 区域内提取灰度共生矩阵 GLCM 特征。

推荐特征：

- contrast：对比度
- energy：能量
- homogeneity：同质性
- correlation：相关性

纹理判断依据：

- 未成熟或成熟香蕉表面通常较平滑。
- 过熟香蕉黑斑较多，纹理更复杂。
- 过熟样本的 contrast 可能更高，homogeneity 可能更低。

### 4.8 人工规则分类

基础版使用人工阈值规则判断成熟度。

示例规则：

if green_ratio > T1:
    result = "unripe"
elif dark_ratio > T2 or glcm_contrast > T3:
    result = "overripe"
else:
    result = "ripe"

阈值 T1、T2、T3 通过实验调试确定。

基础版可以保存每张图片的：

- 原图
- 分割 mask
- 香蕉区域图
- 标注分类结果图
- HSV 和 GLCM 特征值
- 规则分类结果

### 4.9 基础版工作量评估

预计代码量：600-1000 行 Python

预计工作时长：4-6 天

基础版完成后，项目已经具备完整报告展示能力。

## 5. 第二阶段：进阶版机器学习分类方案

### 5.1 阶段目标

进阶版在基础版基础上加入 SVM/KNN 分类器。基础版中的图像预处理、区域分割、颜色特征提取和纹理特征提取模块全部复用。

进阶版新增目标：

- 批量提取图片特征
- 构建特征数据表 CSV
- 划分训练集和测试集
- 特征归一化
- 训练 KNN 和 SVM 分类器
- 输出分类准确率、混淆矩阵和分类报告
- 对比规则分类与机器学习分类效果

### 5.2 进阶版技术路线

图像输入  
→ 图像预处理  
→ 香蕉区域分割  
→ HSV 颜色比例特征提取  
→ GLCM 纹理特征提取  
→ 构建特征向量  
→ 保存特征 CSV  
→ 数据集划分  
→ 特征归一化  
→ 训练 KNN/SVM 分类器  
→ 测试集预测  
→ 模型评估  
→ 输出实验结果

### 5.3 与基础版的衔接关系

基础版已完成并可复用的模块：

- preprocessing.py：图像预处理
- segmentation.py：香蕉区域分割
- morphology.py：形态学处理
- feature_hsv.py：HSV 颜色特征提取
- feature_glcm.py：GLCM 纹理特征提取
- visualization.py：结果可视化

进阶版需要新增的模块：

- dataset_builder.py：批量提取特征并生成 CSV
- ml_classifier.py：SVM/KNN 分类器训练与预测
- evaluation.py：模型评估
- main_ml.py：机器学习版主程序

也就是说，进阶版不是推翻基础版，而是在基础版特征提取能力上增加分类器。

### 5.4 数据集建议

进阶版建议扩充到 90-150 张图片：

- 未成熟：30-50 张
- 成熟：30-50 张
- 过熟：30-50 张

推荐数据划分：

- 训练集：70%
- 测试集：30%

也可采用 5 折交叉验证，提高实验可信度。

### 5.5 特征表设计

每张图片对应一行特征数据。

CSV 示例：

image_path,label,green_ratio,yellow_ratio,dark_ratio,H_mean,H_std,S_mean,S_std,V_mean,V_std,contrast,energy,homogeneity,correlation
data/raw/ripe/001.jpg,ripe,0.02,0.83,0.06,28.5,4.1,132.0,20.3,188.2,31.5,12.4,0.72,0.81,0.64

推荐特征向量：

[
  green_ratio,
  yellow_ratio,
  dark_ratio,
  H_mean,
  H_std,
  S_mean,
  S_std,
  V_mean,
  V_std,
  glcm_contrast,
  glcm_energy,
  glcm_homogeneity,
  glcm_correlation
]

### 5.6 分类器设计

KNN 分类器：

优点：

- 实现简单
- 适合小规模数据集
- 结果容易理解

注意：

- 需要进行特征归一化
- K 值需要调试

SVM 分类器：

优点：

- 小样本场景下效果通常较好
- 适合颜色和纹理组合特征
- 分类边界相对稳定

注意：

- 需要调节核函数、C、gamma 等参数
- 可解释性弱于规则分类

推荐至少对比：

- KNN
- SVM
- 规则分类

### 5.7 实验对比设计

建议设置以下实验：

1. 仅使用 HSV 颜色特征 + KNN/SVM
2. 仅使用 GLCM 纹理特征 + KNN/SVM
3. 使用 HSV + GLCM 组合特征 + KNN/SVM
4. 基础版规则分类
5. 规则分类与机器学习分类结果对比

这样报告中可以分析：

- 颜色特征是否比纹理特征更有效
- 加入纹理特征是否提升过熟香蕉识别效果
- SVM 与 KNN 哪个效果更好
- 机器学习方法相比人工规则是否更稳定

### 5.8 模型评估指标

建议输出：

- Accuracy 准确率
- Precision 精确率
- Recall 召回率
- F1-score
- Confusion Matrix 混淆矩阵
- 错误样例分析

### 5.9 进阶版工作量评估

如果基础版代码模块化完成，进阶版新增工作量：

代码量：300-500 行 Python

新增工作时长：2-3 天

总项目代码量：900-1400 行 Python

总项目工作时长：6-9 天

如果基础版代码没有模块化，后续可能需要额外 1-2 天重构。

## 6. 推荐工程结构目录

推荐项目目录名：banana_ripeness_hgsk

banana_ripeness_hgsk/
│
├── README.md
├── requirements.txt
├── config.yaml
│
├── data/
│   ├── raw/
│   │   ├── unripe/
│   │   ├── ripe/
│   │   └── overripe/
│   │
│   ├── processed/
│   │   ├── masks/
│   │   ├── cropped/
│   │   └── visualized/
│   │
│   └── features/
│       ├── hsv_features.csv
│       ├── glcm_features.csv
│       └── combined_features.csv
│
├── src/
│   ├── main_rule_based.py
│   ├── main_ml.py
│   │
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
│
├── models/
│   ├── svm_model.pkl
│   ├── knn_model.pkl
│   └── scaler.pkl
│
├── results/
│   ├── rule_based/
│   │   ├── images/
│   │   └── summary.csv
│   │
│   ├── machine_learning/
│   │   ├── images/
│   │   ├── confusion_matrix.png
│   │   └── classification_report.txt
│   │
│   └── comparison/
│       └── feature_comparison.csv
│
├── report/
│   ├── figures/
│   └── report.md
│
└── tests/
    └── test_features.py

## 7. 推荐开发顺序

第一步：搭建基础工程

完成：

- 创建项目目录
- 安装依赖
- 准备数据目录
- 整理图片命名规则

第二步：实现基础图像处理流程

完成：

- 图像读取
- 图像预处理
- HSV 转换
- 香蕉区域分割
- 形态学处理
- mask 保存和可视化

第三步：实现基础版规则分类

完成：

- HSV 颜色比例统计
- GLCM 纹理特征提取
- 人工阈值规则分类
- 输出分类结果图和 summary.csv

此时基础版项目已经可作为课程报告提交。

第四步：构建特征数据集

在基础版基础上批量处理所有图片：

- 提取每张图片的 HSV 特征
- 提取每张图片的 GLCM 特征
- 合并为 combined_features.csv
- 检查缺失值和异常样本

第五步：实现进阶版机器学习分类

完成：

- 读取 combined_features.csv
- 划分训练集和测试集
- 特征归一化
- 训练 KNN 分类器
- 训练 SVM 分类器
- 保存模型文件

第六步：实验评估与报告整理

完成：

- 输出准确率
- 输出混淆矩阵
- 输出分类报告
- 对比规则分类、KNN、SVM
- 分析错误样例
- 整理报告图片与实验表格

## 8. 风险与应对

### 8.1 香蕉区域分割不稳定

原因：

- 背景颜色接近香蕉
- 光照变化明显
- 阴影较强

应对：

- 初期使用简单背景拍摄
- 使用 HSV 和 Lab 空间辅助分析
- 加入最大连通区域筛选
- 必要时手动裁剪香蕉主体区域

### 8.2 规则分类阈值不稳定

原因：

- 不同光照下颜色比例变化较大
- 成熟与过熟边界不清楚

应对：

- 增加样本数量
- 调整阈值时记录实验过程
- 在报告中说明规则法的局限
- 使用进阶版机器学习方法改进

### 8.3 机器学习样本量不足

原因：

- 图片数量太少
- 类别不均衡

应对：

- 每类至少 30 张
- 保证三类样本数量接近
- 使用交叉验证
- 避免过多复杂特征导致过拟合

## 9. 最终建议

推荐采用“两阶段递进式”完成本项目：

第一阶段先完成基础版规则分类，确保项目能够完整运行并生成可展示结果。

第二阶段在基础版基础上扩展机器学习分类器，使用 HSV + GLCM 特征训练 KNN/SVM，并与规则分类进行对比。

这种方案风险较低、衔接自然、报告内容完整。即使进阶版时间不足，基础版也可以独立完成课程要求；如果进阶版完成，则项目质量和报告深度都会明显提升。