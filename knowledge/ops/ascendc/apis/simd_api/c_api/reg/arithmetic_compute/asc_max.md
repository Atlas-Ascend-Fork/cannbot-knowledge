---
type: API
title: AscMax
description: 根据mask对源操作数src0、src1按元素求最大值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMax

该接口根据mask，对源操作数src0、src1进行按元素求最大值操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- max(-0, +0) = +0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMax](../../vector_compute/asc_max.md)（`same_topic`）：AscMax 与《AscMax》的实质衔接是：AscMax 在 Reg 上按 mask 逐 lane 取大；Vector 对应入口、scalar 变体和 AscMin 对照分别界定内存层、操作数形态与相反比较方向。
- [AscMaxScalar](asc_max_scalar.md)（`same_topic`）：AscMax 与《AscMaxScalar》的实质衔接是：AscMax 在 Reg 上按 mask 逐 lane 取大；Vector 对应入口、scalar 变体和 AscMin 对照分别界定内存层、操作数形态与相反比较方向。
- [AscMin](asc_min.md)（`same_topic`）：AscMin 与《AscMax》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
<!-- cannbot:related:end -->
