---
type: API
title: __hbleux2
description: 比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbleux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbleux2

功能：比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbleux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于或等于第二个数的结果。特殊值：任一分量含nan→true；±0→true；±inf→符合浮点序关系。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《__hbleux2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbleux2](../../half_type/half2_compare_functions/_hbleux2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hbleux2》补充：比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hblex2](_hblex2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hblex2》补充：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时，返回true。
- [__hleux2](_hleux2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hleux2》补充：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
- [__hleux2_mask](_hleux2_mask.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hleux2_mask》补充：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
<!-- cannbot:related:end -->
