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

- [UnitFlag](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《高级极限打磨》提供“本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag优化、L2Cache优化），深入挖掘硬件性能极限。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Matmul高阶API开启UnitFlag](../../../best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`related`）：高级步骤 8 依赖 UnitFlag 重叠 MMAD 与 FIXPIPE，专项指南提供开关、依赖和验证细节。
- [入门功能落地](getting_started.md)（`related`）：高级篇在中级实现上继续加入大包搬运、LoadData3D、常量 Tiling、UnitFlag 和 L2Cache，是入门到极限优化链的后续验证目标。
- [中级性能优化](intermediate_optimization.md)（`same_topic`）：中级性能优化 与《高级极限打磨》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
<!-- cannbot:related:end -->
