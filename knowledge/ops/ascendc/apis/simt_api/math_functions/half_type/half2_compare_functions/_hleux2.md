---
type: API
title: __hleux2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hleux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hleux2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hleux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于或等于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：x或y任一分量为nan→1；±0→1；(有限值,inf)→1；inf→0；(有限值,-inf)→0；-inf→1；inf→1；-inf→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgeux2](_hgeux2.md)（`related`）：__hleux2 与《__hgeux2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
- [__isnanx2](_isnanx2.md)（`related`）：__hleux2 与《__isnanx2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
- [__hbleux2](_hbleux2.md)（`same_topic`）：__hleux2 与《__hbleux2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
- [__hleux2](../../bfloat16_type/bfloat16x2_compare_functions/_hleux2.md)（`same_topic`）：__hleux2 与《__hleux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hleux2_mask](_hleux2_mask.md)（`same_topic`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《__hleux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
