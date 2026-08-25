---
type: API
title: __heqx2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量相等，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__heqx2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heqx2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量相等，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __heqx2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：0→0xFFFF；nan→0x0000；inf→0xFFFF；-inf→0xFFFF；inf→0x0000；任一分量为nan→0x0000。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__isnanx2](_isnanx2.md)（`related`）：__heqx2_mask 与《__isnanx2》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__hbeqx2](_hbeqx2.md)（`same_topic`）：mask 版本把两个分量编码到位掩码，适合后续位选择而非控制流 bool。
- [__hequx2](_hequx2.md)（`same_topic`）：__hequx2 与《__heqx2_mask》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：__heqx2_mask 与《__hequx2_mask》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__heqx2](_heqx2.md)（`same_topic`）：__heqx2_mask 与《__heqx2》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__heqx2_mask](../../half_type/half2_compare_functions/_heqx2_mask.md)（`same_topic`）：__heqx2_mask 与《__heqx2_mask》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：__heqx2_mask 与《__hnex2_mask》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
<!-- cannbot:related:end -->
