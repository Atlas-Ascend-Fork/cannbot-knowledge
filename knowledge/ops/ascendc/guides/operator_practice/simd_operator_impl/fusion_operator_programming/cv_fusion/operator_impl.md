---
type: Guide
title: 融合算子编程算子实现
description: 下文将以Matmul+LeakyRelu融合算子的实现为例，介绍Mix融合算子的设计和实现流程。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/fusion_operator_programming/cv_fusion/operator_impl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子实现

下文将以Matmul+LeakyRelu融合算子的实现为例，介绍Mix融合算子的设计和实现流程。
算子的设计过程分为算子分析、数据流分析、Tiling策略设计三部分。
## 算子分析
算子分析是指明确算子的数学表达式、输入、输出，核函数的名称等信息。
1.  明确算子的数学表达式及计算逻辑。该算子的计算逻辑为，先进行一个矩阵乘操作，然后将矩阵乘的结果与一个alpha参数进行LeakyRelu操作。数学表达式如下：
2.  明确输入和输出。
-   Matmul+LeakyRelu算子输入为a、b、bias，输出为c。alpha作为激活函数LeakyRelu的系数，为固定值，可以在算子实现中直接使用常数值参与计算。
-   本样例中算子输入a、b支持的数据类型为half（float16），算子输入bias支持的数据类型为float32，算子输出c的数据类型为float32。
-   输入矩阵a的形状为[M，K]，输入矩阵b的形状为[K, N]，输出矩阵c的形状为[M，N]，输入bias的形状为[1, N]。
-   算子输入输出支持的数据格式为：ND。
3.  确定核函数名称和参数。
-   您可以自定义核函数名称，本样例中核函数命名为matmul_leakyrelu_custom。
-   根据对算子输入输出的分析，确定核函数的参数a，b，bias，c；a，b, bias为输入在Global Memory上的内存地址，c为输出在Global Memory上的内存地址。
通过以上分析，得到Ascend C  Matmul+LeakyRelu算子的设计规格如下：
-   算子类型（OpType）：MATMUL_LEAKYRELU
-   算子输入输出：
MATMUL_LEAKYRELU算子输入输出规格
-   核函数名称：matmul_leakyrelu_custom
## 数据流分析
进行算子的数据流分析：数据流向为在Cube核上完成Matmul计算后将数据搬运至Vector核进行LeakyRelu计算。根据上述数据流并结合融合算子的编程范式，规划并行的流水任务。如下图所示：
1.  将输入数据从Global Memory搬运到Cube核。
2.  进行Matmul内部的计算，计算公式和计算示意图如下：
注：bias的shape为[1, N]，对A*B结果矩阵的每一行都采用该bias进行偏置。
3.  将Matmul的计算结果搬运到Vector核。
4.  进行Vector矢量计算，该样例中进行LeakyReLU计算。
Leaky ReLU（带泄露线性整流函数）激活函数，是人工神经网络中一种常用的激活函数，其数学表达式和函数图像如下所示：
5.  将输出结果搬运到Global Memory。
前三步的内容都封装在Matmul高阶API内，本样例中可以简化为3个stage。
