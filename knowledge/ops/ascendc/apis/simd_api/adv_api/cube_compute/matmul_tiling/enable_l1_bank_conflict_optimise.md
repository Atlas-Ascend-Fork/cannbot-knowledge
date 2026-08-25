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
