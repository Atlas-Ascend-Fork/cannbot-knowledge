---
type: API
title: CumSum
description: 对输入二维张量按行或列进行累加和操作，输出每个位置及之前所有行或列元素的累加结果，支持逐行和Sklansky二分两种算法。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/CumSum_interface/CumSum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CumSum

对输入二维张量按行（first轴）或列（last轴）进行累加和操作，输出每个位置及之前所有对应轴元素的累加结果。模板参数T支持half/float。支持两种算法：逐行累加（CUMSUM_ALGORITHM_LINEBYLINE，默认）和Sklansky二分累加（CUMSUM_ALGORITHM_SKLANSKY，基于Sklansky Adder并行前缀和实现，通过并行计算多行加和提升效率）。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetCumSumMaxMinTmpSize获取。

模板参数config为CumSumConfig类型，包含isLastAxis（true按last轴/列累加，false按first轴/行累加）、isReuseSource（预留，传false）、outputLastRow（是否输出最后一行数据）、algorithm（累加算法）。接口参数：dstTensor输出累加结果；lastRowTensor输出最后一行数据（outputLastRow为true时有效）；srcTensor输入；sharedTmpBuffer临时缓存；cumSumInfo为CumSumInfo类型，含outter（外轴长度）和inner（内轴长度），TPosition均支持VECIN/VECCALC/VECOUT。

约束：输入仅支持二维结构；cumSumInfo.inner * sizeof(T)必须是32字节整数倍；cumSumInfo.outter和inner都应大于0，且outter * inner不能大于dstTensor或srcTensor大小；outputLastRow为true时inner不能大于lastRowTensor大小；遵循通用地址对齐约束。
