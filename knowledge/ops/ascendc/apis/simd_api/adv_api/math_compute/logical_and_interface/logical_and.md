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

- [BitwiseAnd](../bitwise_and_interface/bitwise_and.md)（`related`）：BitwiseAnd 对整数每一 bit 做与，LogicalAnd 把零/非零解释为布尔值；两者同名易混但语义不同，按需要位运算还是真值运算选型。
- [GetLogicalAndMaxMinTmpSize](get_logical_and_max_min_tmp_size.md)（`related`）：LogicalAnd 不允许输入输出地址重叠并需要临时空间；该 host 接口给出可正确执行所需的最小/最大 workspace。
- [GetLogicalAndTmpBufferFactorSize](get_logical_and_tmp_buffer_factor_size.md)（`related`）：FactorSize 的 maxLivedNodeCount/extraBuf 用于 Host 侧推算一次 LogicalAnd Kernel 可处理元素数。
- [LogicalAnds](../logical_ands_interface/logical_ands.md)（`related`）：LogicalAnds 与《LogicalAnd》的实质衔接是：LogicalAnds 的 scalar 逻辑与接口、两种临时空间查询直接配套；LogicalAnd 是 tensor-tensor 对应形态。
<!-- cannbot:related:end -->
