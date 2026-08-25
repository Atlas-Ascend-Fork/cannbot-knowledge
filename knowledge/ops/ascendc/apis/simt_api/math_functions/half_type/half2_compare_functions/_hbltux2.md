---
type: API
title: __hbltux2
description: 比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbltux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbltux2

功能：比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbltux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于第二个数的结果。特殊值：两个分量均满足x<y→true；任一分量x≥y→false；任一分量为nan→该分量比较结果为true，但整体结果取决于其余分量；nan→true；±0→false；-inf→true；inf→false；-inf→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hltux2](_hltux2.md)（`related`）：__hltux2 按分量返回 half2 1/0，__hbltux2 把两分量归约为一个 bool；需要逐 lane 结果还是整体条件决定选型。
- [__hbltux2](../../bfloat16_type/bfloat16x2_compare_functions/_hbltux2.md)（`same_topic`）：__hbltux2说明比较两个half2类型数据的两个分量，当两个分量均满足第一个数小于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hbltx2](_hbltx2.md)（`same_topic`）：__hbltx2 与《__hbltux2》的实质衔接是：ordered/unordered 与 bool/mask 形式围绕 half2 小于比较的 NaN 和逐 lane 返回契约互相补足。
- [__hltx2](_hltx2.md)（`same_topic`）：__hltx2 与《__hbltux2》的实质衔接是：__hltx2 返回每 lane 的 0/1 half2，mask 变体返回位图、hblt 变体把两 lane 折叠为 bool；unordered 版本改变 NaN 规则，bfloat16x2 版本保持比较契约但替换元素类型。
<!-- cannbot:related:end -->
