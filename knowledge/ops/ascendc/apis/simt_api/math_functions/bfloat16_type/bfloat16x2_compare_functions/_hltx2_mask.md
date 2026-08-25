---
type: API
title: __hltx2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hltx2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltx2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hltx2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：x<y→0xFFFF；x≥y→0x0000；±0→0x0000；inf→0x0000；-inf→0xFFFF；(正常值,inf))→0xFFFF；(正常值,-inf))→0x0000；任一分量含nan→0x0000。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtx2_mask](_hgtx2_mask.md)（`related`）：小于是相反方向谓词。
- [__hltux2_mask](_hltux2_mask.md)（`related`）：__hltx2_mask 与 __hltux2_mask 返回相同 2×16-bit mask 编码，但 ordered 版遇 NaN 为 0，unordered 版为 0xFFFF。
- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《__hltx2_mask》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbltx2](_hbltx2.md)（`same_topic`）：__hbltx2 与《__hltx2_mask》的衔接是：hbltx2 是 bfloat16x2 的逐 lane 小于比较；half2、unordered 版本以及向量/掩码结果接口明确区分 NaN 处理与返回形态。
- [__hltx2_mask](../../half_type/half2_compare_functions/_hltx2_mask.md)（`same_topic`）：《__hltx2_mask》说明比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。；《__hltx2_mask》说明比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数小于第二个数，则对应16位掩码为0xFFFF，否则为0x0。。二者在该接口是half2有序小于的mask编码；数值返回版、bfloat16x2对应版及unordered版直接核对dtype、NaN和返回编码差异上存在可执行的直接衔接。
<!-- cannbot:related:end -->
