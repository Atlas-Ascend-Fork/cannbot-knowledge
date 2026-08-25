---
type: API
title: __hgtux2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgtux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtux2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hgtux2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：x > y→0xFFFF；x ≤ y→0x0000；±0→0x0000；任一分量含nan→0xFFFF；inf→0xFFFF；-inf→0x0000；(有限正数,inf)→0x0000；(有限正数,-inf)→0xFFFF。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtux2_mask](../../half_type/half2_compare_functions/_hgtux2_mask.md)（`related`）：__hgtux2_mask 与《__hgtux2_mask》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hequx2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgtux2_mask 与《__hgeux2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgeux2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgex2](_hgex2.md)（`same_topic`）：__hgtux2_mask 与《__hgex2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgex2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtux2](_hgtux2.md)（`same_topic`）：__hgtux2_mask 与《__hgtux2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtx2](_hgtx2.md)（`same_topic`）：__hgtux2_mask 与《__hgtx2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtx2_mask](_hgtx2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgtx2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2](_hleux2.md)（`same_topic`）：__hgtux2_mask 与《__hleux2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2_mask](_hleux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hleux2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hltux2_mask](_hltux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hltux2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hneux2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__isnanx2](_isnanx2.md)（`same_topic`）：__hgtux2_mask 与《__isnanx2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
<!-- cannbot:related:end -->
