---
type: API
title: AscHalf2Int16
description: 将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscHalf2Int16

将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int16_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int16](../../vector_compute/asc_half2int16.md)（`same_topic`）：将half类型数据转换为int16_t，并支持多种舍入模式。；将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。。两卡都实现 half 到 int16_t 的多舍入转换，分别面向 A2/A3 UB 向量接口和 950 寄存器接口，后者增加饱和模式与 mask 合同。
<!-- cannbot:related:end -->
