---
type: API
title: __hltux2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hltux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltux2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：bfloat16x2_t __hltux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量为nan→1.0；±0→0；-inf→1.0；-inf→1.0；inf→0；inf→0；(有限值,inf)→1.0；(有限值,-inf)→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtux2](_hgtux2.md)（`related`）：无序小于是相反方向谓词，可用于条件方向对照。
- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《__hltux2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbltux2](_hbltux2.md)（`same_topic`）：__hltux2说明比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
- [__hltux2_mask](_hltux2_mask.md)（`same_topic`）：__hltux2 与 __hltux2_mask 具有相同的 unordered 小于及 NaN=true 语义，但分别返回 bfloat16x2 0/1 与两段 16-bit 掩码。
<!-- cannbot:related:end -->
