---
type: API
title: H2Sqrt
description: 获取输入数据x各元素的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Sqrt

功能：获取输入数据x各元素的平方根。

函数原型：bfloat16x2_t h2sqrt(bfloat16x2_t x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的平方根。本接口受全局饱和模式影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：本接口支持的输入数据各元素范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Rsqrt](h2rsqrt.md)（`related`）：H2Sqrt 返回平方根，H2Rsqrt 返回平方根倒数；归一化公式需要倒数时可避免再除法。
- [H2Sqrt](../../half_type/half2_math_functions/h2sqrt.md)（`related`）：half2 H2Sqrt 与 BF16x2 H2Sqrt 具有相同逐分量开方语义，可按低精度 dtype 迁移。
- [Hsqrt](../bfloat16_math_functions/hsqrt.md)（`same_topic`）：Hsqrt 与《H2Sqrt》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
<!-- cannbot:related:end -->
