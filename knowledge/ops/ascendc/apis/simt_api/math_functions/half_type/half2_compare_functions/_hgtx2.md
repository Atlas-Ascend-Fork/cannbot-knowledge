---
type: API
title: __hgtx2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgtx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtx2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：half2 __hgtx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：±0→0；任一分量为nan→0；inf→1；inf→1；ASCRT_MIN_DENORM_FP16→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtx2](_hbgtx2.md)（`related`）：__hgtx2 按分量返回 half2 的 1/0，而 __hbgtx2 将两个分量合并为单个 bool；后续需要逐 lane 掩码还是整体条件决定选择。
- [__hgtux2](_hgtux2.md)（`same_topic`）：__hgtx2 与《__hgtux2》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtx2 与《__hgtux2_mask》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
- [__hgtx2_mask](_hgtx2_mask.md)（`same_topic`）：__hgtx2 与《__hgtx2_mask》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
- [__hltx2](_hltx2.md)（`same_topic`）：__hgtx2 与《__hltx2》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
- [__isnanx2](_isnanx2.md)（`same_topic`）：__hgtx2 与《__isnanx2》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
<!-- cannbot:related:end -->
