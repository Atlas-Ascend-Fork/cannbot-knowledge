---
type: API
title: __hgeux2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgeux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgeux2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hgeux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：nan→1；(任意值,nan)→1；±0→1；inf→1；inf→1；-inf→0；-inf→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgeux2](_hbgeux2.md)（`related`）：__hgeux2 对每个分量分别返回 1/0 的 half2，而 focal 对两个分量做 all 归约后返回 bool；可据是否需要逐分量 mask 选择。
- [__hleux2](_hleux2.md)（`related`）：__hleux2 与《__hgeux2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
- [__hleux2_mask](_hleux2_mask.md)（`related`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《__hgeux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hgeux2 与《__hgeux2_mask》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__hgex2](_hgex2.md)（`same_topic`）：__hgeux2 与《__hgex2》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hgeux2 与《__hgex2_mask》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__isnanx2](_isnanx2.md)（`same_topic`）：__hgeux2 与《__isnanx2》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
<!-- cannbot:related:end -->
