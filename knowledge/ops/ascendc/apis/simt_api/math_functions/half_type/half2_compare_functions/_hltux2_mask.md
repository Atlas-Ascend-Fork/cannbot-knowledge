---
type: API
title: __hltux2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hltux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltux2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hltux2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：±0→0x0；0→0xFFFF；(正数,0)→0x0；任一值为nan→0xFFFF；inf→0x0；inf→0x0；(有限正数,inf)→0xFFFF；-inf→0xFFFF。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hlex2_mask](_hlex2_mask.md)（`related`）：ordered less-or-equal 在 NaN 时为假，而 hltux2_mask 的 unordered less 在任一 NaN 时为真，适合对照 NaN 分支。
- [__hltx2_mask](_hltx2_mask.md)（`related`）：《__hltx2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。；《__hltux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。。二者在该接口是half2有序小于的mask编码；数值返回版、bfloat16x2对应版及unordered版直接核对dtype、NaN和返回编码差异上存在可执行的直接衔接。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hltux2_mask》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hltux2](_hltux2.md)（`same_topic`）：《__hltux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。；《__hltux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。。二者在该接口实现unordered小于并返回half2数值；mask版、有序小于和反向大于用于核对NaN及返回编码上存在可执行的直接衔接。
- [__hltux2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hltux2_mask.md)（`same_topic`）：__hltux2_mask 的核心契约是“比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF”；__hltux2_mask 补充“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF”。
- [__hltx2](_hltx2.md)（`same_topic`）：__hltx2 与《__hltux2_mask》的实质衔接是：__hltx2 返回每 lane 的 0/1 half2，mask 变体返回位图、hblt 变体把两 lane 折叠为 bool；unordered 版本改变 NaN 规则，bfloat16x2 版本保持比较契约但替换元素类型。
<!-- cannbot:related:end -->
