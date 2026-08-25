---
type: API
title: H2Rint
description: 获取与输入数据各元素最接近的整数，若存在两个同样接近的整数，则取其中的偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2rint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Rint

功能：获取与输入数据各元素最接近的整数，若存在两个同样接近的整数，则取其中的偶数。

函数原型：half2 h2rint(half2 x)

参数：x（输入）源操作数。

返回值：与输入各元素最接近的整数值。本接口受全局饱和寄存器影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；±0.5→0；(1.5,2)→2。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Rint](../../bfloat16_type/bfloat16x2_math_functions/h2rint.md)（`related`）：两者都对 packed 两元素执行 nearest-even 整数化并受全局饱和状态影响，差别仅为 BF16x2 与 half2，可用于 dtype 迁移。
- [H2Trunc](h2trunc.md)（`related`）：H2Trunc 与《H2Rint》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [H2Ceil](h2ceil.md)（`same_topic`）：H2Rint 取最近偶数，H2Ceil 向正无穷取整；两者处理同一 half2 输入并受同一饱和寄存器影响，是精确的舍入语义选择。
- [H2Floor](h2floor.md)（`same_topic`）：H2Rint 取最近偶数，H2Floor 向负无穷取整；二者直接覆盖不同方向的 half2 整数化需求。
<!-- cannbot:related:end -->
