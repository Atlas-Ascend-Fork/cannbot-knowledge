---
type: API
title: bfloat16x2类型比较函数
description: bfloat16x2类型数据的比较函数集合，包括相等、不等、大小比较及掩码版本。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/bfloat16x2_compare_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16x2类型比较函数

提供 bfloat16x2 双分量向量类型的比较运算，涵盖相等（__heqx2）、不等（__hnex2）、大小关系（__hlex2、__hgex2、__hltx2、__hgtx2）等比较操作。每个比较提供有序（u 后缀）和无序两种语义版本，以及 _mask 掩码输出变体。还包含 NaN 判断（__isnanx2）和最值获取（__hmaxx2、__hminx2 及其 _nan 变体）。

<!-- cannbot:related:start -->
## 相关

- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《bfloat16x2类型比较函数》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
<!-- cannbot:related:end -->
