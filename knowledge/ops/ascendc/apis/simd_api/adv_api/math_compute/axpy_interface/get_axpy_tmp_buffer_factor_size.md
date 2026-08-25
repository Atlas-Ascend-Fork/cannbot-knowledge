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

- [Axpy](axpy.md)（`related`）：该因子接口可从固定临时空间反推 Axpy 单次最大处理元素数，用于决定 calCount 分块。
- [Axpy接口](axpy_interface.md)（`related`）：该接口提供 Axpy 的 maxLiveNodeCount/extraBuf，可反推单次最大处理量并指导切块，是 Axpy Tiling 的直接输入。
- [GetAxpyMaxMinTmpSize](get_axpy_max_min_tmp_size.md)（`same_topic`）：GetAxpyMaxMinTmpSize 与《GetAxpyTmpBufferFactorSize》的实质衔接是：Axpy 的 max-min/factor 查询直接服务 Axpy kernel 与 SIMD/C API 实现。
<!-- cannbot:related:end -->
