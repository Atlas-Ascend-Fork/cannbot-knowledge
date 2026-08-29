---
type: API
title: __hltux2
description: 比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hltux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltux2

功能：比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hltux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于第二个数的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：±0→0；nan→1；(任意值,nan)→1；-inf→1；inf→0；-inf→0；inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hltux2_mask](_hltux2_mask.md)（`same_topic`）：功能：比较两个half2类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。；功能：比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。若任一输入的分量为nan，对应16位掩码为0xFFFF。。两端采用相同的 half2 无序小于比较与 NaN 判定，但分别返回 half2 数值结果和 packed unsigned 掩码，联合阅读可按后继计算需要选择结果表示。
<!-- cannbot:related:end -->
