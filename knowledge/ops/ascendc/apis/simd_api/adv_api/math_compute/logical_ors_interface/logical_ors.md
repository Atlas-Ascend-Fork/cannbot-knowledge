---
type: API
title: LogicalOrs
description: 输入矢量每个元素与标量进行或操作，非零视为真
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOrs_interface/LogicalOrs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LogicalOrs

输入矢量每个元素与标量进行逻辑或操作。当数据类型不是bool时，零视为False，非零视为True。支持标量在前和标量在后两种场景，标量支持配置为LocalTensor的单点元素。仅Ascend 950PR/950DT支持。

函数原型：template <const LogicalOrsConfig& config = DEFAULT_LOGICAL_ORS_CONFIG, typename T, typename U, typename S> __aicore__ inline void LogicalOrs(const LocalTensor<T>& dst, const U& src0, const S& src1, const uint32_t count)

模板参数config为LogicalOrsConfig类型，含isReuseSource（预留，传false）和scalarTensorIndex（标量为LocalTensor单点元素时指定其作为左操作数(0)或右操作数(1，默认)）；T为目的操作数数据类型（仅支持bool）；U、S为LocalTensor或标量类型，根据src0/src1自动推导，支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src0、src1为源操作数（标量或LocalTensor矢量/单点元素）；count为参与计算元素个数。

约束：左右操作数必须有一个为矢量，不支持同时为标量；传入LocalTensor单点数据作为标量时scalarTensorIndex需为编译期常量（或constexpr）；不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalOrsMaxMinTmpSize](get_logical_ors_max_min_tmp_size.md)（`related`）：输入矢量每个元素与标量进行逻辑或操作。；host侧Tiling接口，用于获取LogicalOrs接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。计算接口定义 LogicalOrs 的逐元素逻辑或语义，该 Host Tiling 接口提供执行它所需的临时空间上下界。
- [GetLogicalOrsTmpBufferFactorSize](get_logical_ors_tmp_buffer_factor_size.md)（`related`）：输入矢量每个元素与标量进行逻辑或操作。；获取LogicalOrs接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。。计算接口定义 LogicalOrs 的逐元素逻辑或语义，固定临时空间时该接口给出反推单次处理元素数的因子。
<!-- cannbot:related:end -->
