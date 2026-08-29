---
type: API
title: Hlog10
description: 计算half输入数据以10为底的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hlog10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hlog10

功能：获取以10为底，输入数据的对数。

函数原型：half hlog10(half x)

参数：x（输入）源操作数。

返回值：以10为底的x的对数。本接口受全局饱和寄存器的影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
