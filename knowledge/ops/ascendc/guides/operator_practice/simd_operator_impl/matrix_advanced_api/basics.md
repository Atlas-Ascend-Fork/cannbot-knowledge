---
type: Guide
title: SIMD算子实现基础知识
description: '>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。'
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/basics.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础知识

## 矩阵乘法概述
Matmul的计算公式为：C = A * B + bias，其示意图如下。
-   A、B为源操作数，A为左矩阵，形状为[M, K]；B为右矩阵，形状为[K, N]。
-   C为目的操作数，存放矩阵乘结果的矩阵，形状为[M, N]。
-   bias为矩阵乘偏置，形状为[1, N]。对A*B结果矩阵的每一行都采用该bias进行偏置。
## 矩阵乘法数据流
在了解矩阵乘法数据流之前，需要先回顾一下几个重要的存储逻辑位置的概念，逻辑位置和物理存储的映射关系请参考逻辑位置和物理存储的映射关系：
-   搬入数据的存放位置：A1，用于存放整块A矩阵，可类比CPU多级缓存中的二级缓存；
-   搬入数据的存放位置：B1，用于存放整块B矩阵，可类比CPU多级缓存中的二级缓存；
-   搬入数据的存放位置：C1，用于存放整块的矩阵乘偏置Bias矩阵，可类比CPU多级缓存中的二级缓存；
-   搬入数据的存放位置：A2，用于存放切分后的小块A矩阵，可类比CPU多级缓存中的一级缓存；
-   搬入数据的存放位置：B2，用于存放切分后的小块B矩阵，可类比CPU多级缓存中的一级缓存；
-   搬入数据的存放位置：C2，用于存放切分后的小块矩阵乘偏置Bias矩阵，可类比CPU多级缓存中的一级缓存；
-   结果数据的存放位置：CO1，用于存放小块结果C矩阵，可理解为Cube Out；
-   结果数据的存放位置：CO2，用于存放整块结果C矩阵，可理解为Cube Out；
-   搬入数据的存放位置：VECCALC，一般在计算需要临时变量时使用此位置。
矩阵乘法数据流指矩阵乘的输入输出在各存储位置间的流向。逻辑位置的数据流向如下图所示（为了简化描述，没有列出bias）：
-   A矩阵从输入位置到A2的数据流如下（输入位置可以是GM或者VECOUT）：GM->A2，GM->A1->A2；VECOUT->A1->A2。
由于A1比A2的空间更大，数据从GM或VECOUT可以先搬入A1进行缓存，待该数据执行Cube计算前，数据直接从A1搬入A2，这样在搬运大量数据时可以减少计算前的等待时间，提升性能，只有在搬入数据较少的场景才可能使用GM->A2的数据流。
-   B矩阵从输入位置到B2的数据流如下（输入位置可以是GM或者VECOUT）：GM->B2，GM->B1->B2；VECOUT->B1->B2。
由于B1比B2的空间更大，数据从GM或VECOUT可以先搬入B1进行缓存，待该数据执行Cube计算前，数据直接从B1搬入B2，这样在搬运大量数据时可以减少计算前的等待时间，提升性能，只有在搬入数据较少的场景才可能使用GM->B2的数据流。
-   完成A2*B2=CO1计算。
-   CO1数据汇聚到CO2：CO1->CO2。
-   从CO2到输出位置（输出位置可以是GM或者VECIN）：CO2->GM/CO2->VECIN。
## 数据格式
在完成Matmul矩阵乘法时，主要涉及到两种分形格式ND和NZ。其它的数据格式请参考数据排布格式。
-   ND：普通格式，N维张量。
-   NZ：为满足AI Core中Cube计算单元高性能计算的需要，引入该特殊格式。

<!-- cannbot:related:start -->
## 相关

- [Matmul特性介绍](feature_scenarios/matmul_features.md)（`related`）：基础数据流之后需要按输入位置、输出布局、切分与量化需求选择 Matmul 特性；特性页承接这一设计决策。
- [SIMD算子实现概述](../overview.md)（`related`）：SIMD算子实现概述 与《SIMD算子实现基础知识》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [SIMD算子实现耦合模式](../matrix_basic_api/coupled_mode.md)（`related`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《SIMD算子实现基础知识》说明>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [融合算子编程基础知识](../fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《SIMD算子实现基础知识》明确“>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [算子实现](operator_impl.md)（`same_topic`）：算子实现 与《SIMD算子实现基础知识》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
<!-- cannbot:related:end -->
