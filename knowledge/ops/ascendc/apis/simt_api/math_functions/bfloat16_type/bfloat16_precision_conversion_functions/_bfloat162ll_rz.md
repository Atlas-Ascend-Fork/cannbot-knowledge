---
type: API
title: __bfloat162ll_rz
description: 遵循CAST_TRUNC模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162ll_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162ll_rz

遵循CAST_TRUNC模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
函数原型：long long int __bfloat162ll_rz(const bfloat16_t x)
返回值：输入遵循CAST_TRUNC模式转换成的64位有符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float2ll_rz](../../data_type_conversion/type_conversion_functions/_float2ll_rz.md)（`related`）：__float2ll_rz 与《__bfloat162ll_rz》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__bfloat162ll_rd](_bfloat162ll_rd.md)（`same_topic`）：__bfloat162ll_rd说明遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ll_rn](_bfloat162ll_rn.md)（`same_topic`）：__bfloat162ll_rz说明遵循CAST_TRUNC模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ll_rna](_bfloat162ll_rna.md)（`same_topic`）：__bfloat162ll_rna：这些卡保持到long long的转换目标或RNA语义，只切换源类型、有符号性及RD/RN/RU/RZ舍入，可直接核对bfloat16边界值输出。 目标卡《__bfloat162ll_rz》补充：遵循CAST_TRUNC模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ll_ru](_bfloat162ll_ru.md)（`same_topic`）：__bfloat162ll_ru说明遵循CAST_CEIL模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ull_rz](_bfloat162ull_rz.md)（`same_topic`）：__bfloat162ull_rz 与《__bfloat162ll_rz》的实质衔接是：这些转换保持 bfloat16→unsigned long long 并切换舍入模式，或保持 rz 改变源/目标符号与位宽，用于验证 CAST_TRUNC 的确切边界。
- [__half2ll_rz](../../half_type/half_precision_conversion_functions/_half2ll_rz.md)（`same_topic`）：__half2ll_rz 与《__bfloat162ll_rz》的实质衔接是：这些转换保持 half→long long 并切换舍入，或保持 rz 改变源/目标符号；直接用于验证 CAST_TRUNC 的负数和边界行为。
<!-- cannbot:related:end -->
