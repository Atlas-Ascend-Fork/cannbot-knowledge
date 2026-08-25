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

<!-- cannbot:related:start -->
## 相关

- [AscMmad](../../../../../apis/simd_api/c_api/cube_compute/asc_mmad.md)（`explains`）：中级性能优化 与《AscMmad》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [GmL1OrL0DataMove](../../../../../apis/simd_api/basic_api/data_move_guide/gm_l1_or_l0_data_move.md)（`explains`）：中级性能优化 与《GmL1OrL0DataMove》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [L1与L0数据搬运](../../../../../apis/simd_api/basic_api/data_move_guide/l1_l0_data_move.md)（`explains`）：中级性能优化 与《L1与L0数据搬运》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [LoadData](../../../../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_2_d.md)（`explains`）：中级性能优化 与《LoadData》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [Mmad](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`explains`）：中级性能优化 与《Mmad》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [UnitFlag](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_key_features/unit_flag.md)（`explains`）：中级性能优化 与《UnitFlag》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [UnitFlag](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《中级性能优化》提供“本节基于C++ Tensor编程范式，介绍Matmul基础API算子的性能调优方法，通过4个渐进式优化步骤（L1/L0双缓冲机制、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵），展示从基础实现到高性能优化的完整调优路径。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Matmul高阶API开启UnitFlag](../../../best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`related`）：中级性能优化 与《Matmul高阶API开启UnitFlag》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [入门功能落地](getting_started.md)（`related`）：中级篇直接承接入门 Matmul 实现，引入 L1/L0 双缓冲、细粒度同步和多核切分，形成可复现的下一阶段优化路径。
- [高级极限打磨](advanced_extreme_optimization.md)（`same_topic`）：中级性能优化 与《高级极限打磨》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
<!-- cannbot:related:end -->
