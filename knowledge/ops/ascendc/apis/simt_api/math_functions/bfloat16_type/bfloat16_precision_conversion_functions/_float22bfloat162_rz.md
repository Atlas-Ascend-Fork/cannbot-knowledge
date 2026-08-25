---
type: API
title: __float22bfloat162_rz
description: 将float2类型数据的两个分量遵循CAST_TRUNC模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float22bfloat162_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22bfloat162_rz

将float2类型数据的两个分量遵循CAST_TRUNC模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
函数原型：bfloat16x2_t __float22bfloat162_rz(const float2 x)
返回值：将输入的两个分量遵循CAST_TRUNC模式转换成的bfloat16x2_t类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rz](../../half_type/half_precision_conversion_functions/_float22half2_rz.md)（`related`）：两接口都对 float2 两分量采用 CAST_TRUNC，目标分别为 half2 与 bfloat16x2，可按目标精度格式选用。
- [__float22bfloat162_rd](_float22bfloat162_rd.md)（`same_topic`）：两卡同为 float2→bfloat16x2，分别采用 floor 与 toward-zero 截断。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rz》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rna](_float22bfloat162_rna.md)（`same_topic`）：rz 向零舍入。
- [__float22bfloat162_rna_sat](_float22bfloat162_rna_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rz》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_rz_sat](_float22bfloat162_rz_sat.md)（`same_topic`）：两接口均按 RZ 将 float2 转为 bfloat16x2；目标仅多出饱和语义，因此可直接对照 CTRL 饱和设置与特殊值结果。
<!-- cannbot:related:end -->
