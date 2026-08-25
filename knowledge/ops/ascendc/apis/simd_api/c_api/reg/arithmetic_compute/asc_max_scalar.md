---
type: API
title: AscMaxScalar
description: 矢量src的逐个元素与标量value比较取最大值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_max_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMaxScalar

矢量src的逐个元素与标量value比较大小，接着按照对应的比特位将最大值存入dst中。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 输入src为-0、value为+0的情况下，输出dst为 +0。
- mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMaxScalar](../../vector_compute/asc_max_scalar.md)（`related`）：AscMaxScalar 与《AscMaxScalar》的实质衔接是：Reg 与基础 MaxScalar 操作同一 vector-scalar 最大值，MinScalar 给出相反选择边界。
- [AscMinScalar](asc_min_scalar.md)（`related`）：AscMinScalar 与 AscMaxScalar 共享输入、mask 和标量契约并提供相反钳位方向，便于实现上下界 clamp。
- [AscMax](asc_max.md)（`same_topic`）：AscMax 与《AscMaxScalar》的实质衔接是：AscMax 在 Reg 上按 mask 逐 lane 取大；Vector 对应入口、scalar 变体和 AscMin 对照分别界定内存层、操作数形态与相反比较方向。
<!-- cannbot:related:end -->
