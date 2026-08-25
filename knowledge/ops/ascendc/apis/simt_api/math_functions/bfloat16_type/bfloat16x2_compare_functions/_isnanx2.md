---
type: API
title: __isnanx2
description: 判断bfloat16x2_t类型数据的两个分量是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__isnanx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isnanx2

功能：判断bfloat16x2_t类型数据的两个分量是否为nan。

函数原型：bfloat16x2_t __isnanx2(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：判断输入数据各分量是否为nan，为nan时对应分量结果为1.0，否则为0.0。特殊值：nan→1.0；±0→0；±inf→0；±ASCRT_MAX_NORMAL_BF16→0；ASCRT_MIN_DENORM_BF16→0；正常值→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
