---
type: API
title: __hblex2
description: 比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hblex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hblex2

功能：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时，返回true。

函数原型：bool __hblex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于或等于第二个数的结果。特殊值：任一分量含nan→false；inf→true；-inf→true；-inf→true；(正常值,inf)→true；0→true。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hblex2](../../half_type/half2_compare_functions/_hblex2.md)（`related`）：两接口执行相同的双 lane 有序 <= 归约，但数据类型分别为 half2 和 bfloat16x2。
- [__hbleux2](_hbleux2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hblex2》补充：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时，返回true。
- [__hlex2](_hlex2.md)（`same_topic`）：hlex2 返回逐分量结果，而 hblex2 合并成单 bool，按输出粒度选型。
<!-- cannbot:related:end -->
