---
type: API
title: __isnanx2
description: 判断half2类型数据的两个分量是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__isnanx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isnanx2

功能：判断half2类型数据的两个分量是否为nan。

函数原型：half2 __isnanx2(half2 x)

参数：x（输入）源操作数。

返回值：判断输入数据各分量是否为nan，为nan时对应分量结果为1，否则为0。特殊值：nan→1；±0→0；±inf→0；ASCRT_MAX_NORMAL_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
