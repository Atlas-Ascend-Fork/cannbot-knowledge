---
type: API
title: AscInt642int32
description: 将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int642int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt642int32

将int64_t类型的源操作数转换成int32_t类型，并支持不同的饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int32_t、int64_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 当数据写入目的操作数索引为奇数的位置，索引为偶数位置的数值置零。反之亦然。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt322Int64](asc_int322int64.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt322Int64》说明根据mask将src中的int32_t类型元素转换为int64_t类型，结果写入dst，位宽比为1:2。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
- [AscInt322int64](../../vector_compute/asc_int322int64.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt322int64》说明将int32_t类型数据转换为int64_t类型。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
- [AscInt642Float](asc_int642float.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt642Float》说明将int64_t类型数据转换为float，支持多种舍入模式，源操作数与目的操作数位宽比为2:1。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
- [AscInt642int32](../../vector_compute/asc_int642int32.md)（`same_topic`）：两个 AscInt642Int32 入口都把 int64_t 转为 int32_t；Reg 版本用 mask 和饱和控制，Memory Vector 版本用 UB count 调用。
<!-- cannbot:related:end -->
