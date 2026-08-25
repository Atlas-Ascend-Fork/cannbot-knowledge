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

- [GetLogicalXorMaxMinTmpSize](get_logical_xor_max_min_tmp_size.md)（`related`）：《LogicalXor》说明按元素进行逻辑异或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。；《GetLogicalXorMaxMinTmpSize》说明在host侧获取LogicalXor接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在LogicalXor执行接口必须与两个workspace查询在Host Tiling和Kernel调用间成套使用上存在可执行的直接衔接。
- [GetLogicalXorTmpBufferFactorSize](get_logical_xor_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalXorTmpBufferFactorSize 与《LogicalXor》的实质衔接是：factor 查询与 GetLogicalXorMaxMinTmpSize 是同一 LogicalXor 临时空间的两种 Host 侧规划方式，LogicalXor 接口页和算子卡说明该空间由逐元素逻辑异或直接消费。
- [LogicalXor接口](logical_xor_interface.md)（`same_topic`）：《LogicalXor》说明按元素进行逻辑异或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。；《LogicalXor接口》说明按元素进行逻辑异或操作，并提供临时空间大小获取接口。。二者在LogicalXor执行接口必须与两个workspace查询在Host Tiling和Kernel调用间成套使用上存在可执行的直接衔接。
<!-- cannbot:related:end -->
