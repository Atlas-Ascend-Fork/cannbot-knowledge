---
type: API
title: __hneux2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hneux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hneux2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hneux2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：±0→0x0；任一分量含nan→0xFFFF；±inf→0x0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hneux2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hneux2_mask.md)（`related`）：bfloat16x2 同名接口采用相同的 unordered-not-equal 分量 mask 编码，便于跨 half2/bfloat16x2 对照。
- [__hnex2](_hnex2.md)（`related`）：__hneux2_mask说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF；对__hnex2而言，__hnex2 的 mask 重载保持有序不等比较；hneux2 系列则改变为 unordered 语义，NaN 输入下结果不同。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：hequx2_mask 是同一 unordered 比较族的相等谓词，与 hneux2_mask 形成互补条件。
- [__hneux2](_hneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hneux2_mask正文界定“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hneux2_mask正文说明“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
<!-- cannbot:related:end -->
