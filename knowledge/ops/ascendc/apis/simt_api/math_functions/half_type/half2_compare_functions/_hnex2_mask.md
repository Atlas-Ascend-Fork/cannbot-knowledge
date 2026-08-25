---
type: API
title: __hnex2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hnex2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnex2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hnex2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：±0→0x0；任一分量为nan→0x0；±inf→0x0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [half2类型比较函数](half2_compare_functions.md)（`related`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；half2类型比较函数正文说明“提供half2类型数据的分量比较、最值获取与NaN判断接口”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
- [__hbneux2](_hbneux2.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hbneux2正文说明“比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
- [__hbnex2](_hbnex2.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hbnex2正文说明“比较两个half2类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
- [__hlex2_mask](_hlex2_mask.md)（`same_topic`）：__hlex2_mask 与《__hnex2_mask》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__hneux2](_hneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hnex2_mask正文界定“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hneux2_mask正文说明“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
- [__hnex2](_hnex2.md)（`same_topic`）：__hnex2_mask说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0；对__hnex2而言，__hnex2 的 mask 重载保持有序不等比较；hneux2 系列则改变为 unordered 语义，NaN 输入下结果不同。
- [__hnex2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hnex2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hnex2_mask正文说明“比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
<!-- cannbot:related:end -->
