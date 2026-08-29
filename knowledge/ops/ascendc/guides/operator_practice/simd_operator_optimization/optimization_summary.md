---
type: Guide
title: 优化建议总览表（SIMD算子优化）
description: 汇总 SIMD 算子的 Tiling、启动开销、流水编排、内存访问、矢量计算和矩阵计算优化建议。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/optimization_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 优化建议总览表

SIMD算子性能优化建议汇总，按五大分类组织：Tiling策略（核间负载均衡）、头尾开销优化（设置合适的核数和Kernel类型、限制TilingData大小、避免TPipe在对象内创建、删除Workspace冗余操作、设置DCI编译选项）、流水编排（开启DoubleBuffer、启用Iterate异步接口避免AIC/AIV同步）、内存访问（大数据块搬运、GM地址512B对齐、高效搬运API、避免同地址访问、L2 CacheMode配置、Buffer共享复用、避免UB bank冲突）、矢量计算与矩阵计算优化（UB融合、Counter模式、Mask复用、低延迟指令、BT Buffer bias计算、FP Buffer量化等）。
