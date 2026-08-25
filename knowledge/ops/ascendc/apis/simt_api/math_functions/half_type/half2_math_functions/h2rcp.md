---
type: API
title: H2Rcp
description: 获取输入数据x各元素的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2rcp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Rcp

功能：获取输入数据x各元素的倒数。

函数原型：half2 h2rcp(half2 x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的倒数。本接口受全局饱和寄存器影响，。特殊值：0→ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-0→-ASCRT_MAX_NORMAL_FP16；nan→0；inf→0；-inf→-0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Rsqrt](h2rsqrt.md)（`related`）：h2rsqrt 可视为 sqrt 与 reciprocal 的融合目标，h2rcp 用于拆分实现或精度对照。
- [H2Rcp](../../bfloat16_type/bfloat16x2_math_functions/h2rcp.md)（`same_topic`）：H2Rcp 与《H2Rcp》的衔接是：bfloat16 的倒数入口与 H2Rcp 执行同一 reciprocal 操作，可直接对比 half 特殊值在饱和模式下的处理。
<!-- cannbot:related:end -->
