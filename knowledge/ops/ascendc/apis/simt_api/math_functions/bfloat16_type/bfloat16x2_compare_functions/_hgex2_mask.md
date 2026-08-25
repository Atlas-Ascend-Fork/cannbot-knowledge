---
type: API
title: __hgex2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgex2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgex2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hgex2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：x≥y→0xFFFF；x<y→0x0000；±0→0xFFFF；inf→0xFFFF；-inf→0xFFFF；inf→0xFFFF；-inf→0x0000；任一分量含nan→0x0000。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgex2](_hbgex2.md)（`related`）：hgex2_mask 保留两个 lane 的 ordered >= 结果，hbgex2 仅当两 lane 均成立时返回单个 bool，是 mask 的 all 聚合。
- [__hgtx2_mask](_hgtx2_mask.md)（`related`）：大于等于包含等值边界，条件语义不同。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：两卡都返回两个 16 位 >= mask；ordered hgex2_mask 在 NaN lane 返回 0000，unordered hgeux2_mask 返回 FFFF。
- [__hgex2](_hgex2.md)（`same_topic`）：__hgex2 与《__hgex2_mask》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgex2_mask](../../half_type/half2_compare_functions/_hgex2_mask.md)（`same_topic`）：__hgex2_mask 与《__hgex2_mask》的实质衔接是：__hgex2_mask 返回 half2 ordered ≥ 的位图；数值返回版、反向 ≤、unordered ≥ 与 isnan 卡共同核对返回形态和 NaN 为 false/true 的分支。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgex2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hgex2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
