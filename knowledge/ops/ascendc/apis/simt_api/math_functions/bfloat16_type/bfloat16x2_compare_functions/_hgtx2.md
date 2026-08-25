---
type: API
title: __hgtx2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgtx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtx2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __hgtx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→0；inf→1.0；-inf→0；inf→0；±0→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtx2](_hbgtx2.md)（`related`）：__hbgtx2 把两个 ordered > lane 聚合成单 bool，只有两 lane 都成立才为 true；focal 保留逐 lane 1.0/0.0。
- [__hlex2](_hlex2.md)（`related`）：> 是相反方向谓词，可用于条件反转诊断。
- [__hltx2](_hltx2.md)（`related`）：__hltx2 与《__hgtx2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hgtux2](_hgtux2.md)（`same_topic`）：__hgtux2 与 focal 都返回逐 lane bfloat16 结果，但 unordered 版本在 NaN lane 返回 1.0，ordered 版本返回 0.0。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgtx2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtx2_mask](_hgtx2_mask.md)（`same_topic`）：两卡执行相同 ordered 大于比较；focal 返回 bfloat16x2 的 1.0/0.0，mask 版本返回两个 FFFF/0000 半字，决定后续数值计算还是位选择。
<!-- cannbot:related:end -->
