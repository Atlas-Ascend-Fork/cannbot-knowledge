---
type: API
title: __hgeux2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgeux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgeux2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hgeux2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：任一分量含nan→0xFFFF；±0→0xFFFF；inf→0xFFFF；-inf→0x0000。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hleux2_mask](_hleux2_mask.md)（`related`）：<= 与 >= 共享无序 NaN 语义但方向相反，适合上下界条件选择。
- [__hneux2_mask](_hneux2_mask.md)（`related`）：hneux2_mask 是不等谓词；与 >= mask 对照可排查谓词选错和分支反转。
- [__hbgeux2](_hbgeux2.md)（`same_topic`）：__hgeux2_mask说明比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgeux2 与 __hgeux2_mask 对相同 bfloat16x2 输入执行逐 lane unordered ≥；一个返回 1.0/0.0 lane，另一个返回 0xFFFF/0x0000 位掩码。
- [__hgeux2_mask](../../half_type/half2_compare_functions/_hgeux2_mask.md)（`same_topic`）：half2 与 bfloat16x2 版本都生成逐 lane >= 无序 mask，源精度不同。
- [__hgex2](_hgex2.md)（`same_topic`）：__hgex2 与《__hgeux2_mask》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：两卡都返回两个 16 位 >= mask；ordered hgex2_mask 在 NaN lane 返回 0000，unordered hgeux2_mask 返回 FFFF。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgeux2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hgeux2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
