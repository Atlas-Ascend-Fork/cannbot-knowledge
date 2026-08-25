---
type: API
title: __hbgex2
description: 比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbgex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgex2

功能：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时，返回true。

函数原型：bool __hbgex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于或等于第二个数的结果。特殊值：0→true；-0→true；inf→true；-inf→false；任一分量含nan→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgex2_mask](_hgex2_mask.md)（`related`）：hgex2_mask 保留两个 lane 的 ordered >= 结果，hbgex2 仅当两 lane 均成立时返回单个 bool，是 mask 的 all 聚合。
- [__hbgeux2](_hbgeux2.md)（`same_topic`）：__hbgex2：__hbgex2返回“两分量均>=”的 bool；half2同名卡核对类型变体，__hbgeux2核对 unordered NaN语义，__hgex2则对照逐分量向量结果而非 bool 汇总。 目标卡《__hbgeux2》补充：比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hbgex2](../../half_type/half2_compare_functions/_hbgex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hbgex2》明确“比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时，返回true。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hgex2](_hgex2.md)（`same_topic`）：__hbgex2：__hbgex2返回“两分量均>=”的 bool；half2同名卡核对类型变体，__hbgeux2核对 unordered NaN语义，__hgex2则对照逐分量向量结果而非 bool 汇总。 目标卡《__hgex2》补充：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。
<!-- cannbot:related:end -->
