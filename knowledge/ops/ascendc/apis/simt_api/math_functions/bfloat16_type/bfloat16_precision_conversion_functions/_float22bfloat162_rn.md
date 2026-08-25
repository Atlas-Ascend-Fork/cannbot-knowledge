---
type: API
title: __float22bfloat162_rn
description: 将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float22bfloat162_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22bfloat162_rn

将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。
函数原型：bfloat16x2_t __float22bfloat162_rn(const float2 x)
返回值：将输入的两个分量遵循CAST_RINT模式转换成的bfloat16x2类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat1622float2](_bfloat1622float2.md)（`related`）：“__bfloat1622float2”处理将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。；“__float22bfloat162_rn”明确将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。。实质衔接：float2 与 bfloat16x2 的反向转换说明向量打包路径，标量 bfloat16→float 用于核对每个分量的转换语义。
- [__bfloat162bfloat162](_bfloat162bfloat162.md)（`related`）：__float22bfloat162_rn 从两个 float 分量构造 bfloat16x2，而本接口从单个 bfloat16 广播构造，二者输出布局一致。
- [__float22bfloat162_rd](_float22bfloat162_rd.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rd》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rd_sat](_float22bfloat162_rd_sat.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rd_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rn_sat](_float22bfloat162_rn_sat.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rn_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rna](_float22bfloat162_rna.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rna》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rna_sat](_float22bfloat162_rna_sat.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rna_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_ru](_float22bfloat162_ru.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_ru》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_ru_sat](_float22bfloat162_ru_sat.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_ru_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rz](_float22bfloat162_rz.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rz》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rz_sat](_float22bfloat162_rz_sat.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rz_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`same_topic`）：__float22bfloat162_rn 与《__float2bfloat162_rn》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__floats2bfloat162_rn](_floats2bfloat162_rn.md)（`same_topic`）：《__float22bfloat162_rn》明确“将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。”；它与《__floats2bfloat162_rn》的“将输入数据x、y遵循CAST_RINT模式分别转换为bfloat16类型，并填充到bfloat16x2的前后两部分，返回转换后的bfloat16x2类型数据。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
