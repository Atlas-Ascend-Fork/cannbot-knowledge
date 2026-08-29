---
type: API
title: GetCeilTmpBufferFactorSize
description: 获取Ceil接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/GetCeilTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCeilTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Ceil接口，开发者为其预留currBuff大小的空间，利用GetCeilTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetCeilTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Ceil](ceil.md)（`related`）：“该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。”给出 Ceil 临时区容量推导；“用于Ceil内部复杂计算时存储中间变量，由开发者提供。”确认 Ceil 实际消费该临时缓存，因此能直接用于实现时的 tile 上限计算。
<!-- cannbot:related:end -->
