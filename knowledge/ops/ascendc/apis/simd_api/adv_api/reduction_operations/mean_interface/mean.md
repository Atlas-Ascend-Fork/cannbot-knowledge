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

- [ReduceMean](../reduce_mean_interface/reduce_mean.md)（`related`）：ReduceMean 面向更一般的归约参数，而 Mean 固定沿末轴、最多二维；二者的差异直接用于接口选型。
- [GetMeanMaxMinTmpSize](get_mean_max_min_tmp_size.md)（`same_topic`）：Mean 显式 sharedTmpBuffer 重载要求先由 GetMeanMaxMinTmpSize 根据 shape、dtype 和基本块模式取得空间边界，查询结果直接决定调用能否成立。
- [GetMeanTmpBufferFactorSize](get_mean_tmp_buffer_factor_size.md)（`same_topic`）：焦点处理Mean 的 workspace factor 推算；Mean正文界定“沿最后一轴对输入元素求平均值，最多支持二维输入”。候选是 Mean 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Mean接口](mean_interface.md)（`same_topic`）：Mean说明沿最后一轴对输入元素求平均值，最多支持二维输入；对Mean接口而言，Mean 的末轴二维约束与 ReduceMean 的多维 AR/RA 模式不同；两组 workspace 查询决定各自的 Tiling 空间。
<!-- cannbot:related:end -->
