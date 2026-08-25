---
type: API
title: LogicalOr
description: 按元素进行或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOr_interface/LogicalOr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LogicalOr

按元素进行逻辑或操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。

函数原型：template <const LogicalOrConfig& config = DEFAULT_LOGICAL_OR_CONFIG, typename T, typename U> __aicore__ inline void LogicalOr(const LocalTensor<T>& dst, const LocalTensor<U>& src0, const LocalTensor<U>& src1, const uint32_t count)

模板参数config为LogicalOrConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（仅支持bool）；U为源操作数数据类型（支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src0、src1为两个输入源操作数；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalOrMaxMinTmpSize](get_logical_or_max_min_tmp_size.md)（`related`）：LogicalOr 运行前需由 Host 查询最小和最大临时空间，最小值保障正确性并作为 Kernel tiling 参数。
- [LogicalOrs](../logical_ors_interface/logical_ors.md)（`related`）：LogicalOrs 与《LogicalOr》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [LogicalOrs接口](../logical_ors_interface/logical_ors_interface.md)（`related`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOr》说明按元素进行或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [GetLogicalOrTmpBufferFactorSize](get_logical_or_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalOrTmpBufferFactorSize 与《LogicalOr》的实质衔接是：LogicalOr 的 factor 查询需与 MaxMin 查询共同换算 sharedTmpBuffer，LogicalOr Kernel 是唯一直接消费该 tiling 结果的接口。
<!-- cannbot:related:end -->
