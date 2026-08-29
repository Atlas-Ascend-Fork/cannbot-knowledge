---
type: API
title: Mean
description: 沿最后一轴对输入元素求平均值，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Mean_interface/Mean.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Mean

根据最后一轴方向对各元素求平均值。输入为向量时对全部元素求平均，输入为矩阵时沿最后一维对每行求平均。最多支持二维输入。模板参数T支持half/float，accType指定累加类型。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetMeanMaxMinTmpSize获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求时可提升性能；reduceDim指定reduce维度（默认-1为最后一轴）。

接口参数：dstTensor输出；srcTensor输入（内轴长度需32B对齐，不满足时需补齐）；sharedTmpBuffer临时缓存；meanParams含outter（外轴长度）、inner（补齐后内轴元素个数）等信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；内轴长度需32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetMeanMaxMinTmpSize](get_mean_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetMeanMaxMinTmpSize获取。；host侧Tiling接口，用于获取Mean接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。Mean 明确要求用该 Host 查询选择临时空间，二者闭合执行前容量规划。
- [GetMeanTmpBufferFactorSize](get_mean_tmp_buffer_factor_size.md)（`related`）：获取Mean接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetMeanMaxMinTmpSize获取。。factor 查询把固定缓冲换算为 Mean 单次元素数，Mean 接口选择显式缓冲或框架申请，闭合 Kernel 侧空间规划。
<!-- cannbot:related:end -->
