---
type: API
title: __hltx2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hltx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltx2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：half2 __hltx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否满足第一个数小于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：任一分量为nan→0；±0→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
