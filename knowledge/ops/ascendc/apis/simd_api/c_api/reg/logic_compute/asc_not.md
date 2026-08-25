---
type: API
title: AscNot
description: 对源操作数src执行按位取反操作，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_not.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscNot

该接口用于对源操作数src执行按位取反操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscNeg](../arithmetic_compute/asc_neg.md)（`related`）：AscNeg 与《AscNot》的实质衔接是：AscNeg 的 C++/Vector 入口执行算术取负，AscNot 是按位取反的近名反例，可防止把数值负号与 bitwise NOT 混用。
- [AscNot](../../vector_compute/asc_not.md)（`same_topic`）：两个 AscNot 都执行逐元素按位取反；Reg 入口以寄存器 mask 控制 lane，Memory Vector 入口从 UB 按 count 处理。
<!-- cannbot:related:end -->
