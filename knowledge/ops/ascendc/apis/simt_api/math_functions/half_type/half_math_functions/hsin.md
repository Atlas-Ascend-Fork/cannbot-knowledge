---
type: API
title: Half数学函数hsin
description: 获取输入数据的三角函数正弦值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hsin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Half数学函数hsin

功能：获取输入数据的三角函数正弦值。

函数原型：half hsin(half x)

参数：x（输入）源操作数。

返回值：输入数据的三角函数正弦值。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→0；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hsin](../../bfloat16_type/bfloat16_math_functions/hsin.md)（`related`）：两接口都是标量 16 位正弦函数，分别面向 half 与 bfloat16。
- [Half数学函数hcos](hcos.md)（`related`）：hcos 与 hsin 是同一 half 输入的余弦/正弦配对，旋转、相位和 sincos 类计算常同时消费两者。
<!-- cannbot:related:end -->
