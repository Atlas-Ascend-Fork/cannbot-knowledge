---
type: API
title: __hbgeux2
description: 比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbgeux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgeux2

功能：比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbgeux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于或等于第二个数的结果。特殊值：任一分量为 nan→true；inf→true；-inf→false；inf→true；±0→true。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgeux2](_hgeux2.md)（`related`）：__hgeux2 保留两个 lane 的结果，__hbgeux2 只有两 lane 均满足 unordered >= 时才返回单个 bool；后者是前者结果的 all 聚合。
- [__hbgeux2](../../half_type/half2_compare_functions/_hbgeux2.md)（`same_topic`）：__hbgeux2说明比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hbgex2](_hbgex2.md)（`same_topic`）：__hbgex2：__hbgex2返回“两分量均>=”的 bool；half2同名卡核对类型变体，__hbgeux2核对 unordered NaN语义，__hgex2则对照逐分量向量结果而非 bool 汇总。 目标卡《__hbgeux2》补充：比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hgeux2_mask说明比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hbgeux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
