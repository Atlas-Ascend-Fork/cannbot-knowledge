---
type: API
title: __isnanx2
description: 判断bfloat16x2_t类型数据的两个分量是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__isnanx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isnanx2

功能：判断bfloat16x2_t类型数据的两个分量是否为nan。

函数原型：bfloat16x2_t __isnanx2(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：判断输入数据各分量是否为nan，为nan时对应分量结果为1.0，否则为0.0。特殊值：nan→1.0；±0→0；±inf→0；±ASCRT_MAX_NORMAL_BF16→0；ASCRT_MIN_DENORM_BF16→0；正常值→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsNan接口](../../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__isnanx2》提供“判断bfloat16x2_t类型数据的两个分量是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__hbltux2](_hbltux2.md)（`related`）：__isnanx2说明判断bfloat16x2_t类型数据的两个分量是否为nan。
- [__heqx2_mask](_heqx2_mask.md)（`related`）：__heqx2_mask 与《__isnanx2》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__isnanx2](../../half_type/half2_compare_functions/_isnanx2.md)（`related`）：bfloat16x2 同名函数采用相同逐分量 NaN 判定，可对照 half2/bfloat16x2 路径。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__isnanx2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__isnanx2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
