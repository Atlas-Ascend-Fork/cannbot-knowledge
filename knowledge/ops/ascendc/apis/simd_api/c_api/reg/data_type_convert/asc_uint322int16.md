---
type: API
title: AscUint322int16
description: 将uint32_t类型数据转换为int16_t类型，支持饱和与非饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_uint322int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUint322int16

将uint32_t类型数据转为int16_t类型，支持饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 当数据写入目的操作数索引为奇数的位置，索引为偶数位置的数值置零。反之亦然。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt322Int16](asc_int322int16.md)（`related`）：AscInt322Int16 与本接口目标同为 int16 且宽度流相同，源有无符号决定数值解释。
- [AscInt322Uint16](asc_int322uint16.md)（`related`）：AscInt322Uint16 与本接口保持 32→16 位窄化不变、同时交换源与目的的有符号性，可用于区分位宽窄化和符号解释各自的转换约束。
- [AscUint322uint16](asc_uint322uint16.md)（`related`）：AscUint322int16 与 focal 具有相同 uint32 源和 16 位目标宽度，但目标符号性不同，适合对照饱和或截断边界。
<!-- cannbot:related:end -->
