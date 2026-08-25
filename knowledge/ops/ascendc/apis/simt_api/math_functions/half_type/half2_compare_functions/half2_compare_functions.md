---
type: API
title: half2类型比较函数
description: 提供half2类型数据的分量比较、最值获取与NaN判断接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/half2_compare_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half2类型比较函数

提供 half2 双分量向量类型的比较运算，涵盖相等、不等、大小关系等比较操作，每个比较提供有序（u 后缀）和无序两种语义版本，以及 _mask 掩码输出变体。还包含 NaN 判断（__isnanx2）和最值获取（__hmaxx2、__hminx2 及其 _nan 变体），支持两路并行比较。

<!-- cannbot:related:start -->
## 相关

- [__hleux2_mask](_hleux2_mask.md)（`related`）：《__hleux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。；《half2类型比较函数》说明提供half2类型数据的分量比较、最值获取与NaN判断接口。。二者在该mask接口实现unordered <=；数值返回版、有序<=和反向>=用于核对NaN与掩码语义上存在可执行的直接衔接。
- [__hltux2](_hltux2.md)（`related`）：《__hltux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。；《half2类型比较函数》说明提供half2类型数据的分量比较、最值获取与NaN判断接口。。二者在该接口实现unordered小于并返回half2数值；mask版、有序小于和反向大于用于核对NaN及返回编码上存在可执行的直接衔接。
- [__hminx2](_hminx2.md)（`related`）：half2 比较函数总览把 __hminx2、__hmaxx2、NaN 变体及布尔/掩码比较放在同一接口族中，便于按返回语义选型。
- [__hnex2_mask](_hnex2_mask.md)（`related`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；half2类型比较函数正文说明“提供half2类型数据的分量比较、最值获取与NaN判断接口”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
- [half2类型算术函数](../half2_arithmetic_functions/half2_arithmetic_functions.md)（`related`）：half2 算术产生的 packed 结果常需按分量比较、取最值或检查 NaN；比较函数集提供保持 half2 布局的后续条件处理。
- [__hminx2_nan](_hminx2_nan.md)（`same_topic`）：half2 比较函数入口把 __hminx2_nan 与普通 min、max、NaN 判断和有序/无序比较组织在同一选择表中，可定位 focal 的 NaN 传播版本。
<!-- cannbot:related:end -->
