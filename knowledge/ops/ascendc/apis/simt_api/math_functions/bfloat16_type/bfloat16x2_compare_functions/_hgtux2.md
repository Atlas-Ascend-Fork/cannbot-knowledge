---
type: API
title: __hgtux2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgtux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtux2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：bfloat16x2_t __hgtux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→1.0；inf→0；±0→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hltux2](_hltux2.md)（`related`）：无序小于是相反方向谓词，可用于条件方向对照。
- [__hbgtux2](_hbgtux2.md)（`same_topic`）：hgtux2 返回逐分量 bfloat16x2 结果，而 hbgtux2 把两个分量合并为单 bool，按输出粒度选型。
- [__hgtux2](../../half_type/half2_compare_functions/_hgtux2.md)（`same_topic`）：half2 版本执行相同无序大于比较，源精度不同。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgtux2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtx2](_hgtx2.md)（`same_topic`）：__hgtux2 与 focal 都返回逐 lane bfloat16 结果，但 unordered 版本在 NaN lane 返回 1.0，ordered 版本返回 0.0。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hgtux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
