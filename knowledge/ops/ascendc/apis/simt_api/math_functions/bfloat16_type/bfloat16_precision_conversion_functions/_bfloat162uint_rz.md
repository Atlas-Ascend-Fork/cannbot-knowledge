---
type: API
title: __bfloat162uint_rz
description: 遵循CAST_TRUNC模式，将bfloat16类型数据转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162uint_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162uint_rz

遵循CAST_TRUNC模式，将bfloat16类型数据转换为无符号整数，返回转换后的值。
函数原型：unsigned int __bfloat162uint_rz(const bfloat16_t x)
返回值：输入遵循CAST_TRUNC模式转换成的无符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162uint_rd](_bfloat162uint_rd.md)（`same_topic`）：__bfloat162uint_rd 与《__bfloat162uint_rz》的衔接是：这些接口都把浮点半精度值转为无符号整数，候选分别对比源类型及 rn/rd/ru/rz 舍入方向，可直接核对边界输入的转换结果。
- [__bfloat162uint_rn](_bfloat162uint_rn.md)（`same_topic`）：两卡具有相同 bfloat16→uint32 契约，仅分别采用 nearest-even 与 trunc；负数或分数截断语义需显式选型。
- [__bfloat162uint_rna](_bfloat162uint_rna.md)（`same_topic`）：rz 版本向零取整，用于不需要 nearest-away 行为的转换。
- [__bfloat162uint_ru](_bfloat162uint_ru.md)（`same_topic`）：__bfloat162uint_ru 与《__bfloat162uint_rz》的实质衔接是：候选覆盖相同 bfloat16→uint 的 rd/rn/rna/rz 舍入和相同 ru 下的 float/half/signed int 对照，可直接核对 CEIL 边界结果。
- [__bfloat162ull_rz](_bfloat162ull_rz.md)（`same_topic`）：__bfloat162ull_rz 与《__bfloat162uint_rz》的实质衔接是：这些转换保持 bfloat16→unsigned long long 并切换舍入模式，或保持 rz 改变源/目标符号与位宽，用于验证 CAST_TRUNC 的确切边界。
<!-- cannbot:related:end -->
