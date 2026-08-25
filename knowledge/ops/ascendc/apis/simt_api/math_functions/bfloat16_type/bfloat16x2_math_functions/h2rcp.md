---
type: API
title: H2Rcp
description: 获取输入数据x各元素的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2rcp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Rcp

功能：获取输入数据x各元素的倒数。

函数原型：bfloat16x2_t h2rcp(bfloat16x2_t x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的倒数。本接口受全局饱和模式影响，。特殊值：0→ASCRT_MAX_NORMAL_BF16；-0→-0；nan→0；inf→0；-inf→-0。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为±inf。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hrcp](../bfloat16_math_functions/hrcp.md)（`related`）：H2Rcp 是两个 bfloat16 lane 的并行倒数，Hrcp 是标量入口；两者用于按数据是否 packed 选型。
- [H2Rcp](../../half_type/half2_math_functions/h2rcp.md)（`same_topic`）：H2Rcp 与《H2Rcp》的衔接是：bfloat16 的倒数入口与 H2Rcp 执行同一 reciprocal 操作，可直接对比 half 特殊值在饱和模式下的处理。
- [H2Rsqrt](h2rsqrt.md)（`same_topic`）：H2Rsqrt 与《H2Rcp》的实质衔接是：H2Rsqrt 与 sqrt/rcp、half/float Rsqrt 及精度替代卡共同界定倒数平方根实现。
<!-- cannbot:related:end -->
