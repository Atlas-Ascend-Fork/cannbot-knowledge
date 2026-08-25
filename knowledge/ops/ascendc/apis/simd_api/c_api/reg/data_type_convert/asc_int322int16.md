---
type: API
title: AscInt322Int16
description: 根据mask将src中的int32_t类型元素转换为int16_t类型，支持饱和/非饱和模式，结果写入dst，位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int322int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt322Int16

根据mask将src中的每个int32_t类型元素转化为int16_t类型，支持饱和/非饱和模式，结果写入dst。由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。参考伪代码
关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：int16_t、int32_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- mask掩码位为0时，dst对应元素置0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Int32](asc_int162int32.md)（`related`）：Int32→Int16 是该提升转换的反向通路，可核对 1:2 位宽转换的奇偶 lane 和掩码布局。
- [AscInt322Uint16](asc_int322uint16.md)（`related`）：AscInt322Uint16 共享 32→16 位压缩和饱和边界，但目的有符号性不同，适合明确负数处理。
- [AscUint322int16](asc_uint322int16.md)（`related`）：AscInt322Int16 与本接口目标同为 int16 且宽度流相同，源有无符号决定数值解释。
- [AscInt322int16](../../vector_compute/asc_int322int16.md)（`same_topic`）：两个 AscInt322Int16 入口都把 int32_t 转为 int16_t；Reg 版本补充 mask、奇偶 lane 写入及饱和控制，Memory Vector 版本提供 UB count 形式。
<!-- cannbot:related:end -->
