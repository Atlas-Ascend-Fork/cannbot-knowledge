---
type: API
title: __hltx2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hltx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hltx2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __hltx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→0；-inf→1.0；-inf→1.0；inf→0；inf→0；(有限值,inf)→1.0；(有限值,-inf)→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbleux2](_hbleux2.md)（`related`）：__hltx2 与《__hbleux2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbltux2](_hbltux2.md)（`related`）：__hltx2 与《__hbltux2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hbltx2](_hbltx2.md)（`related`）：__hltx2 与《__hbltx2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hgtx2](_hgtx2.md)（`related`）：__hltx2 与《__hgtx2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hltux2](_hltux2.md)（`related`）：__hltx2 与《__hltux2》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hltx2_mask](_hltx2_mask.md)（`related`）：__hltx2 与《__hltx2_mask》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [bfloat16x2类型比较函数](bfloat16x2_compare_functions.md)（`related`）：__hltx2 与《bfloat16x2类型比较函数》的实质衔接是：bfloat16x2 小于比较的数值/掩码返回形式、无序比较及 half2 同名接口决定 NaN 和两个 lane 的判读。
- [__hltx2](../../half_type/half2_compare_functions/_hltx2.md)（`same_topic`）：__hltx2 与《__hltx2》的实质衔接是：__hltx2 返回每 lane 的 0/1 half2，mask 变体返回位图、hblt 变体把两 lane 折叠为 bool；unordered 版本改变 NaN 规则，bfloat16x2 版本保持比较契约但替换元素类型。
<!-- cannbot:related:end -->
