---
type: API
title: AscInt322Uint16
description: 根据mask将src中的int32_t类型元素转换为uint16_t类型，支持饱和模式，结果写入dst，位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int322uint16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscInt322Uint16

根据mask将src中的每个int32_t类型元素转换为uint16_t类型，并支持不同的饱和模式，结果写入dst。由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。参考伪代码
关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：int32_t、uint16_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- mask掩码位为0时，dst对应元素置0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt322Int16](asc_int322int16.md)（`related`）：AscInt322Uint16 共享 32→16 位压缩和饱和边界，但目的有符号性不同，适合明确负数处理。
- [AscUint322int16](asc_uint322int16.md)（`related`）：AscInt322Uint16 与本接口保持 32→16 位窄化不变、同时交换源与目的的有符号性，可用于区分位宽窄化和符号解释各自的转换约束。
- [AscUint322uint16](asc_uint322uint16.md)（`related`）：AscInt322Uint16 与 focal 具有相同目标 uint16，但源端有符号性不同，可对照判断负数和溢出处理。
- [AscInt322int16](../../vector_compute/asc_int322int16.md)（`same_topic`）：AscInt322Uint16 与《AscInt322int16》的实质衔接是：AscInt322Uint16 是 32→16 位窄化并带饱和/奇偶 lane 布局；uint32→uint16 与 int32→int16 对照可分离符号解释和位宽布局。
<!-- cannbot:related:end -->
