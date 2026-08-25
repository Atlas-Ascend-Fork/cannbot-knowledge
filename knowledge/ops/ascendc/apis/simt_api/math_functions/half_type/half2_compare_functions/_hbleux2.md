---
type: API
title: __hbleux2
description: 比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbleux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbleux2

功能：比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbleux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于或等于第二个数的结果。特殊值：x、y的某分量含nan，其余分量均满足x≤y→true；各分量均为nan→true；x、y的分量不含nan且不满足x≤y→false；x、y某分量含nan但另一对应分量不满足x≤y→false；±0→true；((-inf, -inf),(inf, inf))→true；((inf, inf),(-inf, -inf))→false；((±inf, ±inf),(-inf, -inf))→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hleux2_mask](_hleux2_mask.md)（`related`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《__hbleux2》说明比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
- [__isnanx2](_isnanx2.md)（`related`）：__hbleux2 与《__isnanx2》的实质衔接是：half2 unordered LE 布尔接口需与 mask、ordered LE、isnan 和比较入口对照。
- [__hbleux2](../../bfloat16_type/bfloat16x2_compare_functions/_hbleux2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hbleux2》补充：比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hblex2](_hblex2.md)（`same_topic`）：__hbleux2 与《__hblex2》的实质衔接是：half2 unordered LE 布尔接口需与 mask、ordered LE、isnan 和比较入口对照。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hbleux2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
<!-- cannbot:related:end -->
