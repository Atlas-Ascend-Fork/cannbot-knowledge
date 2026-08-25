---
type: API
title: __hnegx2
description: 获取输入half2类型数据各分量的负值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/__hnegx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnegx2

功能：获取输入half2类型数据各分量的负值。

函数原型：half2 __hnegx2(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据各分量的负值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→-ASCRT_MAX_NORMAL_FP16；-inf→ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
