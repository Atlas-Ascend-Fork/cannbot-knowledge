---
type: Guide
title: 中级性能优化
description: 本节基于C++ Tensor编程范式，介绍Matmul基础API算子的性能调优方法，通过4个渐进式优化步骤（L1/L0双缓冲机制、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵），展示从基础实现到高性能优化的完整调优路径。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 中级性能优化

本节基于C++ Tensor编程范式，介绍Matmul基础API算子的性能调优方法，通过4个渐进式优化步骤（L1/L0双缓冲机制、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵），展示从基础实现到高性能优化的完整调优路径。
## 优化路径：
编号：优化手段：等级：定位
1：L1/L0双缓冲Ping-Pong布局：中级：流水线骨架
2：细粒度流水同步：中级：流水线骨架
3：多核并行切分：中级：并行策略
4：DataCopyIn优先搬运B矩阵：中级：调度策略
5：大包搬运：高级：流水线骨架
6：LoadData3D替代LoadData2D：高级：指令队列优化
7：常量Tiling：高级：编译期优化
8：UnitFlag优化：高级：MMAD-FIXPIPE流水重叠
9：L2Cache优化：高级：MTE2带宽压榨
## 从入门到优化
入门功能落地实现了Matmul算子的基本功能：A/B 矩阵经 MTE2 的 DataCopy 从GM搬入L1（ND→NZ转换），经MTE1的 LoadData 搬入L0A/L0B（NZ→ZZ/ZN 转换），Cube单元执行 Mmad，结果经 Fixpipe 从L0C写回GM。
