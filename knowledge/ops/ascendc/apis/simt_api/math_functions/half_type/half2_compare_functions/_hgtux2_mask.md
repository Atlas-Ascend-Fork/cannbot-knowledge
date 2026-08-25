---
type: API
title: __hgtux2_mask
description: 比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgtux2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtux2_mask

功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。

函数原型：unsigned int __hgtux2_mask(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。各分量掩码结果。特殊值：nan→0xFFFF；(任意值,nan)→0xFFFF；-0→0xFFFF；inf→0xFFFF；inf→0xFFFF；inf→0x0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtux2](_hbgtux2.md)（`related`）：__hgtux2_mask 与《__hbgtux2》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hgtux2_mask](../../bfloat16_type/bfloat16x2_compare_functions/_hgtux2_mask.md)（`related`）：__hgtux2_mask 与《__hgtux2_mask》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hltux2](_hltux2.md)（`related`）：《__hltux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。；《__hgtux2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。。二者在该接口实现unordered小于并返回half2数值；mask版、有序小于和反向大于用于核对NaN及返回编码上存在可执行的直接衔接。
- [__isnanx2](_isnanx2.md)（`related`）：__hgtux2_mask 与《__isnanx2》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hgtux2](_hgtux2.md)（`same_topic`）：两者执行同一 unordered greater-than 且 NaN 为真，mask 版本把两个 lane 输出编码为 16bit 掩码而非 half2 的 1/0。
- [__hgtx2](_hgtx2.md)（`same_topic`）：__hgtx2 与《__hgtux2_mask》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
- [__hgtx2_mask](_hgtx2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgtx2_mask》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hltux2_mask](_hltux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hltux2_mask》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
<!-- cannbot:related:end -->
