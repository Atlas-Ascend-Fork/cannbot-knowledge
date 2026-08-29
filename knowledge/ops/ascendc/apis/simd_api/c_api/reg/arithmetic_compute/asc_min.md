---
type: API
title: AscMin
description: 根据mask对源操作数src0、src1按元素求最小值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMin

该接口根据mask，对源操作数src0、src1进行按元素求最小值操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- min(-0, +0) = -0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMinScalar](asc_min_scalar.md)（`same_topic`）：“该接口根据mask，对源操作数src0、src1进行按元素求最小值操作，将结果写入目的操作数dst。”与“根据mask将源操作数src按元素与标量value进行比较，将最小值写入目的操作数dst。”是双方正文中的具体合同。两端都按 mask 计算逐元素最小值，第二操作数分别为矢量 src1 和标量 value，互读能选择输入形态并核对广播行为。
<!-- cannbot:related:end -->
