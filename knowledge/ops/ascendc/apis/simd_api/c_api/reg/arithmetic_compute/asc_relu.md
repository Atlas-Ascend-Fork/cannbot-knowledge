---
type: API
title: AscRelu
description: 根据mask对源操作数src按元素进行relu操作，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscRelu

根据mask对源操作数src进行按元素relu操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int32_t。

约束：mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscRelu](../../vector_compute/asc_relu.md)（`related`）：Reg AscRelu 对寄存器数据执行相同激活，而 Vector AscRelu 直接处理 UB，按数据驻留位置选型。
- [Relu](../../../basic_api/reg_vector_compute/basic_arithmetic/relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；AscRelu正文界定“根据mask对源操作数src按元素进行relu操作，将结果写入目的操作数dst”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
