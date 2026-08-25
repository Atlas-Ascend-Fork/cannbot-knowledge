---
type: API
title: __hlex2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hlex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hlex2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __hlex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于或等于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量为nan→0；±0→1.0；inf→1.0；inf→0；(有限值,inf)→1.0；-inf→1.0；inf→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtx2](_hgtx2.md)（`related`）：> 是相反方向谓词，可用于条件反转诊断。
- [__hlex2](../../half_type/half2_compare_functions/_hlex2.md)（`related`）：bfloat16x2 版本保持相同逐 lane <= 语义，用于跨两种 16bit 浮点输入实现对照。
- [__hblex2](_hblex2.md)（`same_topic`）：hlex2 返回逐分量结果，而 hblex2 合并成单 bool，按输出粒度选型。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hlex2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hlex2_mask](_hlex2_mask.md)（`same_topic`）：Mask 版本输出逐 lane 条件 mask。
<!-- cannbot:related:end -->
