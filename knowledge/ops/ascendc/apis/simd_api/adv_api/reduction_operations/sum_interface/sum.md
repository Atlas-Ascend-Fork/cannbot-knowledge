---
type: API
title: Sum
description: 获取最后一个维度的元素总和，向量输入对各元素相加，矩阵输入沿最后一维度对每行求和，最多支持二维数据。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Sum_interface/Sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Sum

获取最后一个维度的元素总和。输入为向量时对全部元素求和，输入为矩阵时沿最后一维对每行求和。最多支持二维输入。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetSumMaxMinTmpSize获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求时可提升性能；reduceDim指定reduce维度（默认-1为最后一轴）。

接口参数：dstTensor输出；srcTensor输入（内轴长度需32B对齐，不满足时需补齐）；sharedTmpBuffer临时缓存；sumParams含outter（外轴长度）、inner（补齐后内轴元素个数）等信息。

约束：最多支持二维输入；内轴长度需32B对齐；遵循通用地址对齐约束。
