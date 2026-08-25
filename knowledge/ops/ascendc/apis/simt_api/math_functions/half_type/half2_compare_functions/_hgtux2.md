---
type: API
title: __hgtux2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hgtux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtux2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hgtux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：任一分量为nan→1；±0→0；inf→1；-inf→0；inf→0；inf→1；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtux2](_hbgtux2.md)（`related`）：Hbgtux2 将两个 lane 的 unordered greater-than 再做全真归约返回 bool，适合组级分支而非逐 lane 结果。
- [__hltux2](_hltux2.md)（`related`）：《__hltux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。；《__hgtux2》说明比较两个half2类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。。二者在该接口实现unordered小于并返回half2数值；mask版、有序小于和反向大于用于核对NaN及返回编码上存在可执行的直接衔接。
- [__hgtux2](../../bfloat16_type/bfloat16x2_compare_functions/_hgtux2.md)（`same_topic`）：half2 版本执行相同无序大于比较，源精度不同。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：两者执行同一 unordered greater-than 且 NaN 为真，mask 版本把两个 lane 输出编码为 16bit 掩码而非 half2 的 1/0。
- [__hgtx2](_hgtx2.md)（`same_topic`）：__hgtx2 与《__hgtux2》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
<!-- cannbot:related:end -->
