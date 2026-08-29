---
type: API
title: GetAsinTmpBufferFactorSize
description: 获取Asin接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asin_interface/GetAsinTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAsinTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Asin接口，开发者为其预留currBuff大小的空间，利用GetAsinTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetAsinTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuffer（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [GetAsinMaxMinTmpSize](get_asin_max_min_tmp_size.md)（`related`）：通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量；开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。最大/最小接口先确定合法临时空间范围，factor 接口再把已选空间换算成单次元素容量；两端组成 Host Tiling 选 buffer、Kernel 按容量分块的闭环。
<!-- cannbot:related:end -->
