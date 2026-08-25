---
type: API
title: __brev（整数数学函数）
description: 将输入数据的位序反转，返回反转后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__brev.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __brev（整数数学函数）

功能：将输入数据的位序反转，返回反转后的值。

函数原型：unsigned int __brev(unsigned int x)

参数：x（输入）源操作数。

返回值：输入数据的位反转值。当输入的类型为uint32_t时，返回值的第n位对应输入数据的第31-n位；当输入的类型为uint64_t时，返回值的第n位对应输入数据的第63-n位。特殊值：0→0；0→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
