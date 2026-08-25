---
type: API
title: __hgex2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgex2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgex2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hgex2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：任一分量为nan→0x0；±0→0xFFFF；±inf→0xFFFF；inf→0xFFFF；-inf→0x0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgex2](_hbgex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hgex2_mask》明确“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgeux2 与《__hgex2_mask》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hgex2_mask 是 ordered >= 版本；与 unordered 版本的唯一关键差异是 NaN 分量是否置 0xFFFF。
- [__hgex2](_hgex2.md)（`same_topic`）：__hgex2_mask 与《__hgex2》的实质衔接是：__hgex2_mask 返回 half2 ordered ≥ 的位图；数值返回版、反向 ≤、unordered ≥ 与 isnan 卡共同核对返回形态和 NaN 为 false/true 的分支。
- [__hgex2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hgex2_mask.md)（`same_topic`）：__hgex2_mask 与《__hgex2_mask》的实质衔接是：__hgex2_mask 返回 half2 ordered ≥ 的位图；数值返回版、反向 ≤、unordered ≥ 与 isnan 卡共同核对返回形态和 NaN 为 false/true 的分支。
- [__hlex2_mask](_hlex2_mask.md)（`same_topic`）：__hlex2_mask 与《__hgex2_mask》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__isnanx2](_isnanx2.md)（`same_topic`）：__hgex2_mask 与《__isnanx2》的实质衔接是：__hgex2_mask 返回 half2 ordered ≥ 的位图；数值返回版、反向 ≤、unordered ≥ 与 isnan 卡共同核对返回形态和 NaN 为 false/true 的分支。
<!-- cannbot:related:end -->
