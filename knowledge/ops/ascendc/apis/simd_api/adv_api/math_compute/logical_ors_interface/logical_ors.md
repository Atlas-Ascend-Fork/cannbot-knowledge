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

- [GetLogicalOrsMaxMinTmpSize](get_logical_ors_max_min_tmp_size.md)（`related`）：《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递；《LogicalOrs》说明输入矢量每个元素与标量进行或操作，非零视为真。二者在LogicalOrs的Host侧最大/最小临时空间与factor查询共同为同一个Kernel接口确定workspace预算上存在可执行的直接衔接。
- [LogicalOr](../logical_or_interface/logical_or.md)（`related`）：LogicalOrs 与《LogicalOr》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [LogicalOr接口](../logical_or_interface/logical_or_interface.md)（`related`）：LogicalOrs 与《LogicalOr接口》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [GetLogicalOrsTmpBufferFactorSize](get_logical_ors_tmp_buffer_factor_size.md)（`same_topic`）：LogicalOrs 与《GetLogicalOrsTmpBufferFactorSize》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [LogicalOrs接口](logical_ors_interface.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOrs》说明输入矢量每个元素与标量进行或操作，非零视为真。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
