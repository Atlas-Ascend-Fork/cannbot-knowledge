---
type: API
title: 比较与选择概述
description: Compare、Compares称之为比较接口，用于逐元素比较Tensor或Scalar的大小，并根据比较结果生成掩码。Select、GatherMask称之为选择接口，用于根据掩码条件从源操作数中选取元素输出到目的操作数。推荐使用场景如下：
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 比较与选择概述

Compare、Compares称之为比较接口，用于逐元素比较Tensor或Scalar的大小，并根据比较结果生成掩码。Select、GatherMask称之为选择接口，用于根据掩码条件从源操作数中选取元素输出到目的操作数。推荐使用场景如下：

逐元素比较两个tensor大小，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。 支持多种比较模式： - LT：小于（less than） - GT：大于（greater than） - GE：大于或等于（greater than or equal to） - EQ：等于（equal to） - NE：不等于（not equal to） - LE：小于或等于（less than or equal to）

本接口组包含 Compare, Compare（结果存入寄存器）, Compares, Select，辅助接口包括 GetCmpMask(ISASI)。

本接口属于 UB 矢量计算比较与选择接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。；当参数count或repeatTime取值为0时，该接口的行为如下：；针对如下型号，该接口不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [SelectFlexibleScalar](select_flexible_scalar.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《比较与选择概述》提供“Compare、Compares称之为比较接口，用于逐元素比较Tensor或Scalar的大小，并根据比较结果生成掩码。Select、GatherMask称之为选择接口，用于根据掩码条件从源操作数中选取元素输出到目的操作数。推荐使用场景如下：”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
<!-- cannbot:related:end -->
