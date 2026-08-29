---
type: API
title: GetBitwiseAndMaxMinTmpSize
description: 用于在Host侧获取BitwiseAnd接口所需的最大和最小临时空间大小，作为Tiling参数传递到Kernel侧使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseAnd_interface/GetBitwiseAndMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---


# GetBitwiseAndMaxMinTmpSize

Kernel侧BitwiseAnd接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetBitwiseAndMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- ascendcPlatform（输入）：输入的平台信息。PlatformAscendC的定义请参见构造及析构函数。
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为uint16_t，此处应传入2。
- isReuseSource（输入）：该参数预留，传入默认值false即可。
- maxValue（输出）：BitwiseAnd接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性能会有一定程度的优化提升。。

<!-- cannbot:related:start -->
## 相关

- [BitwiseAnd](bitwise_and.md)（`related`）：__aicore__ inline void BitwiseAnd(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)；Kernel侧BitwiseAnd接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小；Kernel API 以 count 定义本次工作量，Host 查询为其底层实现提供合法临时空间范围，调用方据此同时确定分块元素数与 Tiling buffer 容量。
- [GetBitwiseAndTmpBufferFactorSize](get_bitwise_and_tmp_buffer_factor_size.md)（`same_topic`）：Kernel侧BitwiseAnd接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用。；该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。前者按计算规模选择空间，后者在空间固定时反推 tile，闭合同一 BitwiseAnd sharedTmpBuffer sizing 合同。
<!-- cannbot:related:end -->
