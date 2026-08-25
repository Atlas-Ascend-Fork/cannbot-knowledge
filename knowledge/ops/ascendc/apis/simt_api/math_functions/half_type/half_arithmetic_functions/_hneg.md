---
type: API
title: __hneg
description: 获取输入half类型数据的负值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hneg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hneg

功能：获取输入half类型数据的负值。

函数原型：half __hneg(const half x)

参数：x（输入）源操作数。

返回值：输入数据的负值。本接口受全局饱和模式影响，。特殊值：±0→∓0；±inf→∓ASCRT_MAX_NORMAL_FP16；nan→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__habs](_habs.md)（`related`）：HNeg 改符号，HAbs 清除数值符号；负零/NaN 语义需分别验证。
- [__hsub](_hsub.md)（`related`）：取负常用于 x-y = x+(-y)，但直接 HSub 的舍入链不同。
- [__hneg](../../bfloat16_type/bfloat16_arithmetic_functions/_hneg.md)（`same_topic`）：bfloat16 版本执行同一取负，源精度不同。
<!-- cannbot:related:end -->
