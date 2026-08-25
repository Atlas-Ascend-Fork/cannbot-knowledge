---
type: Guide
title: Matmul性能优化策略总览
description: 本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各分类的简介请参见如下表格，详细内容请阅读后续章节。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_optimization_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul性能优化策略总览

本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各分类的简介请参见如下表格，详细内容请阅读后续章节。
-   Tiling优化
Tiling优化策略总览
-   并行度优化
并行度优化策略总览
-   内存优化
内存优化策略总览
-   Scalar优化
Scalar优化策略总览
-   搬运优化
搬运优化策略总览

<!-- cannbot:related:start -->
## 相关

- [MC²算子性能调优案例](../mc_operator_tuning.md)（`related`）：《MC²算子性能调优案例》的任务是“MC2通算融合算子性能调优案例，通过数据切分实现计算与通信流水掩盖，介绍切分策略制定与优化方法。”。《Matmul性能优化策略总览》具体提供“本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各分类的简介请参见如下表格，详细内容请阅读后续章节。”，它直接用于MC2 通算融合的 Matmul 性能入口和 MC2 原型配置。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](matmul_ibshare_b.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul性能优化策略总览》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [AOT编译优化（高级编程）](../../../programming_guide/advanced_programming/aot_compilation_optimization.md)（`same_topic`）：AOT编译优化（高级编程）：AOT把典型Tiling常量化并在host按配置选择特化kernel；编译加速页给构建上下文，多分支策略承接运行时选择，Matmul优化页对应正文点名示例。 目标卡《Matmul性能优化策略总览》补充：本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各分类的简介请参见如下表格，详细内容请阅读后续章节。
<!-- cannbot:related:end -->
