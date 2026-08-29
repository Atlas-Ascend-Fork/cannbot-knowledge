---
type: API
title: __heqx2
description: 比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__heqx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heqx2

功能：比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。

函数原型：half2 __heqx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：x=y→1；x≠y→0；0→1；inf→1；-inf→1；inf→0；nan→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：“功能：比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。”与“功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。”提供双方正文证据。两端都逐分量判断 half2 相等，但 heqx2 返回 half2 数值 1.0/0.0，hequx2_mask 返回打包位掩码并规定 NaN 行为；这正是调用端选择结果表示的同一比较主题。
<!-- cannbot:related:end -->
