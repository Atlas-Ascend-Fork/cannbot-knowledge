---
type: API
title: EnableL1BankConflictOptimise
description: 根据GetTiling接口计算出的Tiling参数，获取是否可以开启L1 Bank冲突优化功能。若可以开启该功能，则与TilingKey机制配合使用，通过增加TilingKey，关联Host侧与Kernel侧实现，并在Kernel侧增加代码实现分支，将MatmulConfig中的enableL1BankConflictOptimise设置为true，即可优化L1上的Bank冲突。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/EnableL1BankConflictOptimise.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# EnableL1BankConflictOptimise

根据GetTiling接口计算出的Tiling参数，获取是否可以开启L1 Bank冲突优化功能。若可以开启该功能，则与TilingKey机制配合使用，通过增加TilingKey，关联Host侧与Kernel侧实现，并在Kernel侧增加代码实现分支，将MatmulConfig中的enableL1BankConflictOptimise设置为true，即可优化L1上的Bank冲突。

返回值：- false：Kernel侧不能开启L1 Bank冲突优化。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《EnableL1BankConflictOptimise》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：EnableL1BankConflictOptimise 与《sub-kernel 后缀 _N 是 tilingKey 位编码非序号》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：EnableL1BankConflictOptimise 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [避免bank冲突（NPU架构版本2201）](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md)（`explains`）：EnableL1BankConflictOptimise 与《避免bank冲突（NPU架构版本2201）》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [避免bank冲突（NPU架构版本3510）](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_3510.md)（`explains`）：EnableL1BankConflictOptimise 与《避免bank冲突（NPU架构版本3510）》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GetTiling](get_tiling.md)（`related`）：EnableL1BankConflictOptimise 与《GetTiling》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：EnableL1BankConflictOptimise 与《Matmul Tiling类使用说明》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [MatmulConfig](../matmul_kernel/matmul_config.md)（`related`）：EnableL1BankConflictOptimise 与《MatmulConfig》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [SetMatmulConfigParams](set_matmul_config_params.md)（`related`）：EnableL1BankConflictOptimise 与《SetMatmulConfigParams》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：EnableL1BankConflictOptimise 与《TCubeTiling结构体》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
<!-- cannbot:related:end -->
