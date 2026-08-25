---
type: API
title: H2Log
description: 获取以e为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log

功能：获取以e为底，输入数据各元素的对数。

函数原型：bfloat16x2_t h2log(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：以e为底的输入数据各元素的对数。本接口受全局饱和模式影响，。特殊值：0→-ASCRT_MAX_NORMAL_BF16；-0→-ASCRT_MAX_NORMAL_BF16；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log10](h2log10.md)（`related`）：H2Log10 与 H2Log 共享 bfloat16x2 饱和和特殊值处理，仅对数底分别为 10 与 e；并读可按公式底数选型。
- [H2Log](../../half_type/half2_math_functions/h2log.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log》补充：获取以e为底，输入数据各元素的对数。
<!-- cannbot:related:end -->
