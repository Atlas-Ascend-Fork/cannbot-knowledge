---
type: API
title: LogicalXor
description: 按元素进行逻辑异或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalXor_interface/LogicalXor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LogicalXor

按元素进行逻辑异或操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。

函数原型：template <const LogicalXorConfig& config = DEFAULT_LOGICAL_XOR_CONFIG, typename T, typename U> __aicore__ inline void LogicalXor(const LocalTensor<T>& dst, const LocalTensor<U>& src0, const LocalTensor<U>& src1, const uint32_t count)

模板参数config为LogicalXorConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（仅支持bool）；U为源操作数数据类型（支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src0、src1为两个输入源操作数；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalXorMaxMinTmpSize](get_logical_xor_max_min_tmp_size.md)（`related`）：计算接口以“count为参与计算元素个数。”消费分块长度；Host 查询接口说明“host侧Tiling接口，用于获取LogicalXor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”，先约束 UB 预算再确定 Kernel 分块。
- [GetLogicalXorTmpBufferFactorSize](get_logical_xor_tmp_buffer_factor_size.md)（`related`）：Factor 查询卡指出“获取LogicalXor接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。”；计算卡的调用参数规定“count为参与计算元素个数。”，前者正是为后者的 count 分块提供容量上限。
<!-- cannbot:related:end -->
