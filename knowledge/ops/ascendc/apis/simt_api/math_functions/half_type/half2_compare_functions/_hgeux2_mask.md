---
type: API
title: __hgeux2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgeux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgeux2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hgeux2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：nan→0xFFFF；(任意值,nan)→0xFFFF；-0→0xFFFF；inf→0xFFFF；inf→0xFFFF。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgeux2](_hbgeux2.md)（`related`）：__hbgeux2 将两分量 predicate 汇总为单 bool，适合整体条件判断而非逐分量 mask。
- [__hgex2](_hgex2.md)（`related`）：__hgex2 与《__hgeux2_mask》的实质衔接是：half2 ordered GE 的 mask/bool 形态和 unordered 变体围绕逐 lane 返回与 NaN 规则互补，isnan 明确特殊值分支。
- [__hleux2_mask](_hleux2_mask.md)（`related`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《__hgeux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgeux2 与《__hgeux2_mask》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__hgeux2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hgeux2_mask.md)（`same_topic`）：half2 与 bfloat16x2 版本都生成逐 lane >= 无序 mask，源精度不同。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hgex2_mask 是 ordered >= 版本；与 unordered 版本的唯一关键差异是 NaN 分量是否置 0xFFFF。
<!-- cannbot:related:end -->
