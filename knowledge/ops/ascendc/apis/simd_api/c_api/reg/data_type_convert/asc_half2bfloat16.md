---
type: API
title: AscHalf2Bfloat16
description: 将half类型数据转为bfloat16类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscHalf2Bfloat16

将half类型数据转为bfloat16类型，并支持多种舍入模式。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、half。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [__half2bfloat16_rd](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_half2bfloat16_rd.md)（`related`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《AscHalf2Bfloat16》具体提供“将half类型数据转为bfloat16类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
- [__half2bfloat16_rn](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_half2bfloat16_rn.md)（`related`）：SIMT 标量接口以 RN 模式完成 half→bfloat16，而 focal 在 RegTensor 上向量化转换；两者帮助按执行模型与舍入要求选型。
- [__half2bfloat16_ru](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_half2bfloat16_ru.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《AscHalf2Bfloat16》明确提供“将half类型数据转为bfloat16类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
<!-- cannbot:related:end -->
