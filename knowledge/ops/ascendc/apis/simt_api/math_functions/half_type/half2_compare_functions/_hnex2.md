---
type: API
title: __hnex2
description: 比较两个half2类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hnex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnex2

功能：比较两个half2类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。

函数原型：half2 __hnex2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：0→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbnex2](_hbnex2.md)（`related`）：__hnex2 保留每个分量的比较结果为 half2，而 __hbnex2 再把两个分量归约成一个 bool；两者适用于不同的后续分支粒度。
- [__hneux2_mask](_hneux2_mask.md)（`related`）：__hneux2_mask说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF；对__hnex2而言，__hnex2 的 mask 重载保持有序不等比较；hneux2 系列则改变为 unordered 语义，NaN 输入下结果不同。
- [__hneux2](_hneux2.md)（`same_topic`）：__hnex2 与 __hneux2 都对 half2 做逐 lane不等比较；区别是 NaN 时 ordered 与 unordered 版本的真值规则。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：__hnex2_mask说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0；对__hnex2而言，__hnex2 的 mask 重载保持有序不等比较；hneux2 系列则改变为 unordered 语义，NaN 输入下结果不同。
<!-- cannbot:related:end -->
