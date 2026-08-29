---
type: Guide
title: 高级极限打磨
description: 本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag优化、L2Cache优化），深入挖掘硬件性能极限。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/advanced_extreme_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 高级极限打磨

本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag优化、L2Cache优化），深入挖掘硬件性能极限。
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
## 从中级到高级
中级性能优化通过L1/L0双缓冲、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵四个步骤，构建了基本的流水线骨架和并行计算框架，实现了MTE2、MTE1、Cube、Fixpipe四个硬件单元的流水并行。

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](intermediate_optimization.md)（`related`）：本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag优化、L2Cache优化），深入挖掘硬件性能极限。；本节基于C++ Tensor编程范式，介绍Matmul基础API算子的性能调优方法，通过4个渐进式优化步骤（L1/L0双缓冲机制、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵），展示从基础实现到高性能优化的完整调优路径。。高级指南明确建立在中级四步优化之上，再追加五项极限打磨；中级指南定义前置的流水、同步、分核和搬运基础，二者组成同一 Matmul 基础 API 的递进调优路线。
<!-- cannbot:related:end -->
