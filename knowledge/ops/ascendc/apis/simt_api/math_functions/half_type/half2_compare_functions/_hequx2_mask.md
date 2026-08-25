---
type: API
title: __hequx2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hequx2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequx2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hequx2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：任一分量为nan→0xFFFF；±0→0xFFFF；inf→0xFFFF；-inf→0xFFFF；±inf→0xFFFF。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hequx2](_hequx2.md)（`same_topic`）：__hequx2 与《__hequx2_mask》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__heqx2_mask 与《__hequx2_mask》的实质衔接是：ordered equality 的 mask、bool 与 unordered 形态围绕 half2 的逐 lane 返回及 NaN 规则互补。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：hequx2_mask 是同一 unordered 比较族的相等谓词，与 hneux2_mask 形成互补条件。
<!-- cannbot:related:end -->
