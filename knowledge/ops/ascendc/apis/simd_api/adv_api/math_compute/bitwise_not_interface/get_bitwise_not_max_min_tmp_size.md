---
type: API
title: GetBitwiseNotMaxMinTmpSize
description: 用于在Host侧获取BitwiseNot接口所需的最大和最小临时空间大小，作为Tiling参数传递到Kernel侧使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseNot_interface/GetBitwiseNotMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---


# GetBitwiseNotMaxMinTmpSize

Kernel侧BitwiseNot接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetBitwiseNotMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- ascendcPlatform（输入）：输入的平台信息。PlatformAscendC的定义请参见构造及析构函数。
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为uint16_t，此处应传入2。
- isReuseSource（输入）：该参数预留，传入默认值false即可。
- maxValue（输出）：BitwiseNot接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性能会有一定程度的优化提升。。

<!-- cannbot:related:start -->
## 相关

- [BitwiseNot](bitwise_not.md)（`same_topic`）：逐比特对输入进行取反。；Kernel侧BitwiseNot接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小；BitwiseNot 计算卡定义逐比特取反与整型 dtype，Host 查询卡为该 Kernel 计算准备平台、shape 和类型相关的临时空间区间。
- [GetBitwiseNotTmpBufferFactorSize](get_bitwise_not_tmp_buffer_factor_size.md)（`same_topic`）：“开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用”先确定 BitwiseNot 可用的临时空间；“通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量”再把选定空间换算成单次分块上限。
<!-- cannbot:related:end -->
