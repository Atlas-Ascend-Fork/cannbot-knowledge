---
type: API
title: Log2f
description: 获取以2为底输入数据的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log2f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log2f

功能：获取以2为底，输入数据的对数。

函数原型：float log2f(float x)

参数：x（输入）源操作数。

返回值：以2为底的x的对数。特殊值：inf→inf；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hlog2](../bfloat16_type/bfloat16_math_functions/hlog2.md)（`related`）：《Hlog2》说明计算bfloat16_t输入数据以2为底的对数。；《Log2f》说明获取以2为底输入数据的对数。。二者在Hlog2的底数、输入宽度和向量宽度可由同dtype的Log/Log10及half/float对应接口直接对照上存在可执行的直接衔接。
- [Hlog2](../half_type/half_math_functions/hlog2.md)（`related`）：Hlog2 与《Log2f》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
- [H2Log2](../bfloat16_type/bfloat16x2_math_functions/h2log2.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《Log2f》明确“获取以2为底输入数据的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
- [H2Log2](../half_type/half2_math_functions/h2log2.md)（`same_topic`）：Log2f说明获取以2为底输入数据的对数。
<!-- cannbot:related:end -->
