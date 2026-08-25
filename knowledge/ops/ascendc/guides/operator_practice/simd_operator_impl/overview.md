---
type: Guide
title: SIMD算子实现概述
description: Ascend C的算子实现主要包含两个部分：
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

Ascend C的算子实现主要包含两个部分：

-   Host侧Tiling实现

    由于NPU中AI Core内部存储无法完全容纳算子输入输出的所有数据，需要每次搬运一部分输入数据进行计算然后搬出，再搬运下一部分输入数据进行计算，这个过程就称之为Tiling。切分数据的算法称为Tiling算法或者Tiling策略。根据算子的shape等信息来确定数据切分算法相关参数（比如每次搬运的块大小，以及总共循环多少次）的计算程序，称之为Tiling实现，也叫Tiling函数（Tiling Function）。由于Tiling实现中完成的均为标量计算，AI Core并不擅长，所以我们将其独立出来放在Host侧CPU上执行。

-   Device侧Kernel实现

    Kernel实现即算子核函数实现，在Kernel函数内部通过解析Host侧传入的Tiling结构体获取Tiling信息，根据Tiling信息控制数据搬入搬出Local Memory的流程；通过调用计算、数据搬运、内存管理、任务同步API，实现算子逻辑。其核心逻辑基本上都为计算密集型任务，需要在NPU上执行。

本章介绍矢量编程、矩阵编程、融合算子编程三种典型场景下的算子Tiling、Kernel实现，是对上文中典型编程范式的具体应用，同时也介绍了编程的更多细节、API的使用方法等。

<!-- cannbot:related:start -->
## 相关

- [AI Core SIMD编程模型概述](../../programming_guide/programming_model/ai_core_simd_programming/overview.md)（`related`）：SIMD算子实现概述 与《AI Core SIMD编程模型概述》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [SIMD算子实现基础知识](matrix_advanced_api/basics.md)（`related`）：SIMD算子实现概述 与《SIMD算子实现基础知识》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [SIMD算子实现概述](vector_programming/multi_core_tiling/overview.md)（`related`）：SIMD算子实现概述 与《SIMD算子实现概述》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [SIMD算子实现概述](vector_programming/overview.md)（`related`）：SIMD算子实现概述 与《SIMD算子实现概述》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [算子实现](matrix_advanced_api/operator_impl.md)（`related`）：算子实现 与《SIMD算子实现概述》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
<!-- cannbot:related:end -->
