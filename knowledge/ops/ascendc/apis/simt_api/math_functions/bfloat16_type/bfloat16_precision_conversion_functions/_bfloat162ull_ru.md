---
type: API
title: __bfloat162ull_ru
description: 遵循CAST_CEIL模式，将bfloat16类型数据转换为64位无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162ull_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162ull_ru

遵循CAST_CEIL模式，将bfloat16类型数据转换为64位无符号整数，返回转换后的值。
函数原型：unsigned long long int __bfloat162ull_ru(const bfloat16_t x)
返回值：输入遵循CAST_CEIL模式转换成的64位无符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__half2ull_ru](../../half_type/half_precision_conversion_functions/_half2ull_ru.md)（`related`）：half 源的 ru 版本目标和舍入方向相同，但源精度/范围不同。
- [__bfloat162ull_rd](_bfloat162ull_rd.md)（`same_topic`）：rd 与 ru 都做 bfloat16→ull，但向下/向上舍入在非整数值上形成边界两端。
- [__bfloat162ull_rn](_bfloat162ull_rn.md)（`same_topic`）：__bfloat162ull_rn 与《__bfloat162ull_ru》的实质衔接是：这些转换卡保持目标 unsigned long long 或舍入到最近的契约，仅改变 bfloat16 的舍入模式或源类型；有符号 long long 入口用于核对目标符号语义。
- [__bfloat162ull_rna](_bfloat162ull_rna.md)（`same_topic`）：两卡同为 bfloat16→unsigned long long，rna 与向正无穷 ru 在非整数输入上给出不同上界选择。
- [__bfloat162ull_rz](_bfloat162ull_rz.md)（`same_topic`）：__bfloat162ull_rz 与《__bfloat162ull_ru》的实质衔接是：这些转换保持 bfloat16→unsigned long long 并切换舍入模式，或保持 rz 改变源/目标符号与位宽，用于验证 CAST_TRUNC 的确切边界。
<!-- cannbot:related:end -->
