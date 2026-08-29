---
type: Guide
title: 入门功能落地
description: 本节以Add（向量加法）算子为例，介绍基于Ascend C编程模型实现向量算子的基本方法，帮助开发者快速入门SIMD算子开发。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/add_vector_operator/getting_started.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 入门功能落地

本节以Add（向量加法）算子为例，介绍基于Ascend C编程模型实现向量算子的基本方法，帮助开发者快速入门SIMD算子开发。
## 算子概述
Add算子实现两个向量的逐元素加法运算，计算公式为：

- x：输入，shape为[8, 2048]，数据类型为float；
- y：输入，shape为[8, 2048]，数据类型为float；
- z：输出，shape为[8, 2048]，数据类型为float；
样例运行参数：使用8个核完成计算，每个核处理2048个float元素（blockLength = 2048），数据总量为16384个float元素。
## 算子实现
Add算子的计算逻辑遵循"搬入-计算-搬出"三段式流水结构：
1. 将输入数据x和y从GM（Global Memory，芯片外部全局内存）搬运到UB（Unified Buffer，向量计算专用片上缓存）；
2. 在UB上对xLocal、yLocal执行向量加法操作，计算结果存储在zLocal中；
3. 将计算结果从UB搬运回GM。
前置说明：
- GM（Global Memory）：AI Core外部的全局存储，数据通过GlobalTensor访问，容量大但访问速度较慢。
- UB（Unified Buffer）：AI Core内部的向量计算专用缓存，数据通过LocalTensor访问，容量有限但访问速度快。
- DataCopy：用于在GM和UB之间搬运数据的API。
- PipeBarrier：流水线同步屏障，确保数据搬运完成后再执行后续操作。
- block_idx：通过GetBlockIdx()获取当前核编号，用于多核并行时的数据分片。

<!-- cannbot:related:start -->
## 相关

- [基础矢量算子](../../../simd_operator_impl/vector_programming/basic_vector_operator.md)（`same_topic`）：“完成核函数的内部实现，包括3个基本任务：CopyIn，Compute，CopyOut”给出基础矢量算子的实现骨架，“Add算子的计算逻辑遵循"搬入-计算-搬出"三段式流水结构”提供该骨架的具体 Add 落地。
<!-- cannbot:related:end -->
