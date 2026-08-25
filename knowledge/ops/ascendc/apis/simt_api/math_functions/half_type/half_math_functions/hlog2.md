---
type: API
title: Hlog2
description: 计算half输入数据以2为底的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hlog2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hlog2

功能：获取以2为底，输入数据的对数。

函数原型：half hlog2(half x)

参数：x（输入）源操作数。

返回值：以2为底的x的对数。本接口受全局饱和寄存器的影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；nan→0；inf→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hlog10](hlog10.md)（`related`）：Hlog2 提供以 2 为底的同 dtype 标量对数，与 Hlog10 共同覆盖按公式底数选型。
- [Hlog2](../../bfloat16_type/bfloat16_math_functions/hlog2.md)（`related`）：Hlog2 与《Hlog2》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
- [Log2f](../../float_math_functions/log2f.md)（`related`）：Hlog2 与《Log2f》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
- [H2Log2](../../bfloat16_type/bfloat16x2_math_functions/h2log2.md)（`same_topic`）：《H2Log2》处理“获取以2为底，输入数据各元素的对数。”。《Hlog2》明确“计算half输入数据以2为底的对数。”，可直接用于核对packed half2 log2 与标量 half/float log2 的同一逐 lane 数学语义。
- [H2Log2](../half2_math_functions/h2log2.md)（`same_topic`）：Hlog2 与《H2Log2》的实质衔接是：Hlog2 与 log/log10、packed/float Log2 和 half 数学库共同定义二进制对数。
<!-- cannbot:related:end -->
