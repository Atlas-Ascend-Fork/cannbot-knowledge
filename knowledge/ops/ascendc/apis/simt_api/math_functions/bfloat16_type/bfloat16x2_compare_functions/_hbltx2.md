---
type: API
title: __hbltx2
description: 比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbltx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbltx2

功能：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于第二个数时，返回true。

函数原型：bool __hbltx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于第二个数的结果。特殊值：任一分量含nan→false；inf→false；(正常值,inf)→true；-inf→true；±0→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《__hbltx2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbltux2](_hbltux2.md)（`same_topic`）：__hbltx2 与《__hbltux2》的衔接是：hbltx2 是 bfloat16x2 的逐 lane 小于比较；half2、unordered 版本以及向量/掩码结果接口明确区分 NaN 处理与返回形态。
- [__hbltx2](../../half_type/half2_compare_functions/_hbltx2.md)（`same_topic`）：__hbltx2 与《__hbltx2》的衔接是：hbltx2 是 bfloat16x2 的逐 lane 小于比较；half2、unordered 版本以及向量/掩码结果接口明确区分 NaN 处理与返回形态。
- [__hltx2_mask](_hltx2_mask.md)（`same_topic`）：__hbltx2 与《__hltx2_mask》的衔接是：hbltx2 是 bfloat16x2 的逐 lane 小于比较；half2、unordered 版本以及向量/掩码结果接口明确区分 NaN 处理与返回形态。
<!-- cannbot:related:end -->
