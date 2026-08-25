---
type: API
title: Half数学函数hlog
description: 获取以e为底，输入数据的对数。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hlog.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Half数学函数hlog

功能：获取以e为底，输入数据的对数。

函数原型：half hlog(half x)

参数：x（输入）源操作数。

返回值：以e为底的x的对数。本接口受全局饱和寄存器的影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hlog](../../bfloat16_type/bfloat16_math_functions/hlog.md)（`related`）：bfloat16 Hlog 与 half Hlog 数学语义相同但精度和特殊值范围不同，可用于 dtype 路径迁移。
- [Hlog10](hlog10.md)（`related`）：Hlog 与 Hlog10 处理相同 half 标量和相同饱和/特殊值域，但底数分别为 e 与 10；数学公式换底时必须区分。
<!-- cannbot:related:end -->
