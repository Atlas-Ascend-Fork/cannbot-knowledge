---
type: API
title: __heqx2
description: 比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__heqx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heqx2

功能：比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。

函数原型：half2 __heqx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：x=y→1；x≠y→0；0→1；inf→1；-inf→1；inf→0；nan→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbeqx2](_hbeqx2.md)（`related`）：__heqx2 返回逐 lane 的 half2 0/1 结果，而 focal 把两 lane 归约为单个 bool；输出形态差异决定后续分支或向量计算选型。
- [__hneux2](_hneux2.md)（`related`）：__hneux2 是逐分量 unordered 不等对偶，明确 NaN 时结果为 1，避免用 __heqx2 简单取反而丢失 NaN 语义。
- [__hequx2](_hequx2.md)（`same_topic`）：__hequx2 与《__heqx2》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__heqx2](../../bfloat16_type/bfloat16x2_compare_functions/_heqx2.md)（`same_topic`）：half2 版本执行相同逐 lane 相等比较，输入 dtype 不同。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__heqx2_mask 与《__heqx2》的实质衔接是：ordered equality 的 mask、bool 与 unordered 形态围绕 half2 的逐 lane 返回及 NaN 规则互补。
<!-- cannbot:related:end -->
