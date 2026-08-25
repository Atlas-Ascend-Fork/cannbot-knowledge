---
type: API
title: GetBitwiseXorTmpBufferFactorSize
description: 获取BitwiseXor接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseXor_interface/GetBitwiseXorTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetBitwiseXorTmpBufferFactorSize

该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用BitwiseXor接口，开发者为其预留currBuff大小的空间，利用GetBitwiseXorTmpBufferFactorSize接口得到maxLivedNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetBitwiseXorTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform,const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：
- ascendcPlatform（输入）：输入的平台信息。PlatformAscendC的定义请参见构造及析构函数。
- typeSize（输入）：输入的数据类型大小，单位为字节。
- maxLivedNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [BitwiseXor](bitwise_xor.md)（`related`）：factor 接口给出 maxLivedNodeCount 与 extraBuf，可由已分配空间反算 BitwiseXor 单次 count，补足分块 tiling 公式。
- [GetBitwiseXorMaxMinTmpSize](get_bitwise_xor_max_min_tmp_size.md)（`same_topic`）：GetBitwiseXorMaxMinTmpSize 与《GetBitwiseXorTmpBufferFactorSize》的实质衔接是：GetBitwiseXorMaxMinTmpSize 给出 BitwiseXor 可用临时空间范围，factor 查询在固定空间下反推元素数，Kernel 是该空间的实际消费方。
<!-- cannbot:related:end -->
