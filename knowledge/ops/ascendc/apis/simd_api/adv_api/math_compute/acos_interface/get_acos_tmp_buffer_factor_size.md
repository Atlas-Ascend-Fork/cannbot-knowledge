---
type: API
title: GetAcosTmpBufferFactorSize
description: 获取Acos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acos_interface/GetAcosTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAcosTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Acos接口，开发者为其预留currBuff大小的空间，利用GetAcosTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetAcosTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuffer（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Acos](acos.md)（`same_topic`）：该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。 临时空间大小BufferSize的获取方式请参考GetAcosMaxMinTmpSize。 因子接口从已有 Buffer 反推 calCount，Acos 本体消费由 Tiling 确定的 sharedTmpBuffer，二者闭合缓存与分块配置。
<!-- cannbot:related:end -->
