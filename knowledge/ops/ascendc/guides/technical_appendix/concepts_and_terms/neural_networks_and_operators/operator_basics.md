---
type: Guide
title: 算子基本概念
description: 算子（Operator，简称OP），是深度学习算法中执行特定数学运算或操作的基础单元，例如激活函数（如ReLU）、卷积（Conv）、池化（Pooling）以及归一化（如Softmax）。通过组合这些算子，可以构建神经网络模型。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/neural_networks_and_operators/operator_basics.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子基本概念

算子（Operator，简称OP），是深度学习算法中执行特定数学运算或操作的基础单元，例如激活函数（如ReLU）、卷积（Conv）、池化（Pooling）以及归一化（如Softmax）。通过组合这些算子，可以构建神经网络模型。
本章节介绍算子中常用的基本概念。
## 算子名称（Op Name）
算子的名称，用于标识网络中的某个算子，同一网络中算子的名称需要保持唯一。如下图所示Conv1、Pool1、Conv2都是此网络中的算子名称，其中Conv1与Conv2算子的类型为Convolution，表示分别做一次卷积运算。
## 算子类型（Op Type）
网络中每一个算子根据算子类型进行算子实现的匹配，相同类型算子的实现逻辑相同。在一个网络中同一类型的算子可能存在多个，例如上图中的Conv1算子与Conv2算子的类型都为Convolution。
## 张量（Tensor）
Tensor是算子计算数据的容器，包含如下属性信息。
Tensor属性信息
## 形状（Shape）
张量的形状，以(D0, D1,…,Dn-1)的形式表示，D0到Dn是任意的正整数。
如形状(3,4)表示第一维有3个元素，第二维有4个元素，(3,4)表示一个3行4列的矩阵数组。
形状的第一个元素对应张量最外层中括号中的元素个数，形状的第二个元素对应张量中从左边开始数第二个中括号中的元素个数，依此类推。例如：
张量的形状举例
物理含义我们应该怎么理解呢？假设我们有这样一个shape=(4, 20, 20, 3)。
假设有一些照片，每个像素点都由红/绿/蓝3色组成，即shape里面3的含义，照片的宽和高都是20，也就是20*20=400个像素，总共有4张的照片，这就是shape=(4, 20, 20, 3)的物理含义。
如果体现在编程上，可以简单把shape理解为操作Tensor的各层循环，比如我们要对shape=(4, 20, 20, 3)的A tensor进行操作，循环语句如下：
## 轴（axis）
轴是相对shape来说的，轴代表张量的shape的下标，比如张量a是一个5行6列的二维数组，即shape是(5,6)，则axis=0表示是张量中的第一维，即行。axis=1表示是张量中的第二维，即列。
例如张量数据[[[1,2],[3,4]], [[5,6],[7,8]]]，Shape为(2,2,2)，则轴0代表第一个维度的数据即[[1,2],[3,4]]与[[5,6],[7,8]]这两个矩阵，轴1代表第二个维度的数据即[1,2]、[3,4]、[5,6]、[7,8]这四个数组，轴2代表第三个维度的数据即1，2，3，4，5，6，7，8这八个数。
轴axis可以为负数，此时表示是倒数第axis个维度。
N维Tensor的轴有：0 , 1, 2,……，N-1。

<!-- cannbot:related:start -->
## 相关

- [数据排布格式](data_layout.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《数据排布格式》补充：数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
- [算子功能设计](../../../programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_function_design.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《算子功能设计》补充：本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
- [算子原型定义](../../../programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《算子原型定义》补充：本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
<!-- cannbot:related:end -->
