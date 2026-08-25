---
type: API
title: __hlex2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hlex2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hlex2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hlex2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于或等于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：nan→0x0；(任意值,nan)→0x0；inf→0xFFFF；inf→0x0；-inf→0xFFFF；-inf→0xFFFF；-0→0xFFFF；ASCRT_MAX_NORMAL_FP16→0xFFFF。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hblex2](_hblex2.md)（`related`）：__hlex2_mask 与《__hblex2》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__hltux2_mask](_hltux2_mask.md)（`related`）：ordered less-or-equal 在 NaN 时为假，而 hltux2_mask 的 unordered less 在任一 NaN 时为真，适合对照 NaN 分支。
- [__isnanx2](_isnanx2.md)（`related`）：__hlex2_mask 与《__isnanx2》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hlex2_mask 与《__hgex2_mask》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__hleux2_mask](_hleux2_mask.md)（`same_topic`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《__hlex2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
- [__hlex2](_hlex2.md)（`same_topic`）：__hlex2 与 __hlex2_mask 都对 half2 执行逐 lane ordered ≤；一个返回 half2 的 1/0，另一个返回每 lane 16-bit 掩码。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：__hlex2_mask 与《__hnex2_mask》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
<!-- cannbot:related:end -->
