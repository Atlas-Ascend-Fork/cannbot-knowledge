---
type: API
title: GetAxpyTmpBufferFactorSize
description: 获取Axpy接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Axpy_interface/GetAxpyTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAxpyTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Axpy接口，开发者为其预留currBuff大小的空间，利用GetAxpyTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetAxpyTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Axpy](axpy.md)（`related`）：源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。；该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。；Axpy 的 Tiling 需要确定 calCount，factor helper 由固定 buffer 反推单次元素数，连接 Host 分块与 Device 调用规模。
<!-- cannbot:related:end -->
