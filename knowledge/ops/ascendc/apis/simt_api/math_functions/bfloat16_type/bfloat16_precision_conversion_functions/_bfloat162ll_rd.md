---
type: API
title: __bfloat162ll_rd
description: 遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162ll_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162ll_rd

遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
函数原型：long long int __bfloat162ll_rd(const bfloat16_t x)
返回值：输入遵循CAST_FLOOR模式转换成的64位有符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__half2ll_rd](../../half_type/half_precision_conversion_functions/_half2ll_rd.md)（`related`）：bfloat16 源的同向转换具有不同精度范围。
- [__half2ull_rd](../../half_type/half_precision_conversion_functions/_half2ull_rd.md)（`related`）：__half2ull_rd 与《__bfloat162ll_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__bfloat162ll_rn](_bfloat162ll_rn.md)（`same_topic`）：__bfloat162ll_rd说明遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ll_rna](_bfloat162ll_rna.md)（`same_topic`）：__bfloat162ll_rna：这些卡保持到long long的转换目标或RNA语义，只切换源类型、有符号性及RD/RN/RU/RZ舍入，可直接核对bfloat16边界值输出。 目标卡《__bfloat162ll_rd》补充：遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
- [__bfloat162ll_ru](_bfloat162ll_ru.md)（`same_topic`）：rd 与 ru 对同一 bfloat16→int64 转换分别向负/正无穷取整，可给出结果上下界。
- [__bfloat162ll_rz](_bfloat162ll_rz.md)（`same_topic`）：__bfloat162ll_rd说明遵循CAST_FLOOR模式，将bfloat16类型数据转换为64位有符号整数，返回转换后的值。
<!-- cannbot:related:end -->
