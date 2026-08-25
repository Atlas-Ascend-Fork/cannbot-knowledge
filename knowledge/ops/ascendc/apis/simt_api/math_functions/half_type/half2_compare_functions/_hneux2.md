---
type: API
title: __hneux2
description: 比较两个half2类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hneux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hneux2

功能：比较两个half2类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hneux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：0→0；inf→0；-inf→0；inf→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__heqx2](_heqx2.md)（`related`）：__hneux2 是逐分量 unordered 不等对偶，明确 NaN 时结果为 1，避免用 __heqx2 简单取反而丢失 NaN 语义。
- [__isnanx2](_isnanx2.md)（`related`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__isnanx2正文界定“判断half2类型数据的两个分量是否为nan”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hbneux2](_hbneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hbneux2正文界定“比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hneux2](../../bfloat16_type/bfloat16x2_compare_functions/_hneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hneux2正文界定“比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hneux2_mask正文界定“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hnex2](_hnex2.md)（`same_topic`）：__hnex2 与 __hneux2 都对 half2 做逐 lane不等比较；区别是 NaN 时 ordered 与 unordered 版本的真值规则。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hnex2_mask正文界定“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
<!-- cannbot:related:end -->
