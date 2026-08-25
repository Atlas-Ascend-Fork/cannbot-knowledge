---
type: API
title: 类型转换
description: Memory矢量计算类型转换接口索引页，包含Cast与Truncate(ISASI)。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/type_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 类型转换

提供 Cast 和 Truncate(ISASI) 两个 Memory 矢量计算类型转换接口。

Cast 根据源/目的操作数数据类型进行精度转换，支持浮点转整数、浮点转浮点、整数转浮点、整数转整数，通过 RoundMode 控制舍入模式，支持前 n 个数据计算和高维切分计算（含 mask 逐 bit/连续模式）。Truncate(ISASI) 将浮点数元素截断到整数位，保持原数据类型不变，支持 CAST_RINT、CAST_ROUND、CAST_FLOOR、CAST_CEIL、CAST_TRUNC 五种舍入模式。Truncate(ISASI) 仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Cast](cast.md)（`related`）：Cast 在源/目的 dtype 间转换精度并按 RoundMode 舍入，是需要改变数据类型时的具体入口。
- [精度转换（数据结构）](../../data_structures/precision_conversion.md)（`related`）：精度转换（数据结构） 与《类型转换》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
<!-- cannbot:related:end -->
