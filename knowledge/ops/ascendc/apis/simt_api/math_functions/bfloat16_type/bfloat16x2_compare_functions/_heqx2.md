---
type: API
title: __heqx2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__heqx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heqx2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __heqx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：nan→0；(任意值,nan)→0；nan→0；inf→1.0；-inf→1.0；inf→0；0→1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbequx2](_hbequx2.md)（`same_topic`）：无序相等变体在 NaN 处理上不同；包含 NaN 的测试必须按所需谓词选择。
- [__hbeqx2](_hbeqx2.md)（`same_topic`）：__heqx2 返回逐分量比较结果，而 __hbeqx2 把两分量合并为单 bool；二者按输出粒度选型。
- [__hequx2](_hequx2.md)（`same_topic`）：__hequx2 与《__heqx2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__heqx2](../../half_type/half2_compare_functions/_heqx2.md)（`same_topic`）：half2 版本执行相同逐 lane 相等比较，输入 dtype 不同。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__heqx2_mask 与《__heqx2》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
<!-- cannbot:related:end -->
