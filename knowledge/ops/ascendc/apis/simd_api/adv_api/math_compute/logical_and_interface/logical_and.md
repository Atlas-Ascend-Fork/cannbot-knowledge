---
type: API
title: LogicalAnd
description: 按元素进行与操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalAnd_interface/LogicalAnd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# LogicalAnd

按元素进行逻辑与操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。

函数原型：template <const LogicalAndConfig& config = DEFAULT_LOGICAL_AND_CONFIG, typename T, typename U> __aicore__ inline void LogicalAnd(const LocalTensor<T>& dst, const LocalTensor<U>& src0, const LocalTensor<U>& src1, const uint32_t count)

模板参数config为LogicalAndConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（仅支持bool）；U为源操作数数据类型（支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src0、src1为两个输入源操作数；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalAndMaxMinTmpSize](get_logical_and_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取LogicalAnd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；按元素进行逻辑与操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。。Host 侧 tmp-size 查询为 kernel 侧 LogicalAnd 分配临时空间并选择 tiling 参数，直接支撑该逐元素逻辑与调用。
- [GetLogicalAndTmpBufferFactorSize](get_logical_and_tmp_buffer_factor_size.md)（`related`）：按元素进行逻辑与操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。；获取LogicalAnd接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。。LogicalAnd 是计算接口，Factor 接口直接为它在固定 sharedTmpBuffer 下反推单次处理元素数。
<!-- cannbot:related:end -->
