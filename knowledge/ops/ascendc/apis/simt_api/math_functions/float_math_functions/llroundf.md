---
type: API
title: Llroundf
description: 获取对输入数据四舍五入后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/llroundf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Llroundf

功能：获取对输入数据四舍五入后的整数。

函数原型：long long int llroundf(float x)

参数：x（输入）源操作数。

返回值：对输入四舍五入后的整数。特殊值：nan→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Roundf](roundf.md)（`related`）：Roundf 保持浮点返回值而 Llroundf 直接产生 long long，二者适合后续仍需浮点或需要整数索引的不同链路。
- [Lroundf](lroundf.md)（`same_topic`）：Lroundf 与《Llroundf》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
<!-- cannbot:related:end -->
