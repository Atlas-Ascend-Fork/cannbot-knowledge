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

- [BitwiseOrTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/bitwise_or_tensor_950.md)（`related`）：若 `P=BOOL`，源码改提交 `LogicalOr`；零视为False，非零视为True；算子 BOOL Route 直接切换到 LogicalOr 语义。
- [GetLogicalOrTmpBufferFactorSize](get_logical_or_tmp_buffer_factor_size.md)（`related`）：获取LogicalOr接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素进行逻辑或操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。。FactorSize 的输出专门用于规划 LogicalOr 单次计算量，LogicalOr 页定义被规划的 Kernel 运算及平台范围。
- [GetLogicalOrMaxMinTmpSize](get_logical_or_max_min_tmp_size.md)（`same_topic`）：获取LogicalOr接口所需的最大和最小临时空间大小；按元素进行逻辑或操作；连接 Host 临时空间生产与 Kernel 计算。
<!-- cannbot:related:end -->
