---
type: API
title: __hisinf
description: 判断浮点数是否为无穷。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hisinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hisinf

功能：判断浮点数是否为无穷。

函数原型：bool __hisinf(half x)

参数：x（输入）源操作数。

返回值：返回是否为无穷的结果。输入为非无穷返回false，输入为±inf返回true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Isinf](../../float_math_functions/isinf.md)（`related`）：Isinf 与《__hisinf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
- [__hisinf](../../bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《__hisinf》明确“判断浮点数是否为无穷。”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
