---
type: API
title: GetBitwiseNotTmpBufferFactorSize
description: 获取maxLivedNodeCount和extraBuf，在固定空间大小下推算BitwiseNot算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseNot_interface/GetBitwiseNotTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetBitwiseNotTmpBufferFactorSize

该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用BitwiseNot接口，开发者为其预留currBuff大小的空间，利用GetBitwiseNotTmpBufferFactorSize接口得到maxLivedNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetBitwiseNotTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform,const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：
- ascendcPlatform（输入）：输入的平台信息。PlatformAscendC的定义请参见构造及析构函数。
- typeSize（输入）：输入的数据类型大小，单位为字节。
- maxLivedNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [BitwiseNot接口](bitwise_not_interface.md)（`related`）：FactorSize 用 live-node/extraBuf 模型补充 BitwiseNot 固定 UB 下的 calCount 规划。
- [BitwiseNot](bitwise_not.md)（`same_topic`）：GetBitwiseNotTmpBufferFactorSize 与《BitwiseNot》的实质衔接是：BitwiseNot 的 factor 查询与 MaxMin 查询及 kernel 调用配套，才能确定 sharedTmpBuffer 大小。
- [GetBitwiseNotMaxMinTmpSize](get_bitwise_not_max_min_tmp_size.md)（`same_topic`）：GetBitwiseNotTmpBufferFactorSize 与《GetBitwiseNotMaxMinTmpSize》的实质衔接是：BitwiseNot 的 factor 查询与 MaxMin 查询及 kernel 调用配套，才能确定 sharedTmpBuffer 大小。
- [LogicalNot](../logical_not_interface/logical_not.md)（`same_topic`）：LogicalNot 与《GetBitwiseNotTmpBufferFactorSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
<!-- cannbot:related:end -->
