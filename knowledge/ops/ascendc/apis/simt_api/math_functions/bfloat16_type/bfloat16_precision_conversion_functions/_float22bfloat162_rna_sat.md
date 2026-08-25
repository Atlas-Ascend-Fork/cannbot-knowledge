---
type: API
title: __float22bfloat162_rna_sat
description: 饱和模式下，将float2类型数据的两个分量遵循CAST_ROUND模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float22bfloat162_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22bfloat162_rna_sat

饱和模式下，将float2类型数据的两个分量遵循CAST_ROUND模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
函数原型：bfloat16x2_t __float22bfloat162_rna_sat(const float2 x)
返回值：饱和模式下将输入的两个分量遵循CAST_ROUND模式转换成的bfloat16x2_t类型数据。特殊值如下：
约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。；SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat1622float2](_bfloat1622float2.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__bfloat1622float2》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rd](_float22bfloat162_rd.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rd》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rd_sat](_float22bfloat162_rd_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rd_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rna_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rn_sat](_float22bfloat162_rn_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rn_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rna](_float22bfloat162_rna.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rna》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_ru](_float22bfloat162_ru.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_ru》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_ru_sat](_float22bfloat162_ru_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_ru_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rz](_float22bfloat162_rz.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rz》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rz_sat](_float22bfloat162_rz_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rz_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float2bfloat16_rna_sat](_float2bfloat16_rna_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float2bfloat16_rna_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
<!-- cannbot:related:end -->
