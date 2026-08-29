---
type: API
title: Matmul Kernel侧接口
description: 提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Matmul_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul Kernel侧接口

提供矩阵乘计算的 Kernel 侧接口，通过模板参数与 MatmulConfig 配置矩阵排布、数据类型及计算模式。
核心流程为 Init 初始化后，使用 SetTensorA/SetTensorB 设置左右矩阵，SetTensorScaleA/SetTensorScaleB 设置量化缩放因子，SetBias/SetAntiQuantScalar 等设置偏置与反量化参数，再经 Iterate/IterateAll/IterateBatch 执行计算，最后 GetTensorC/AsyncGetTensorC 获取结果。
支持多种配置获取方法（GetNormalConfig、GetMDLConfig、GetIBShareNormConfig 等）适配不同硬件特性，并提供 SetHF32、SetQuantVector、SetSparseIndex 等高级特性开关。
REGIST_MATMUL_OBJ 宏用于注册 Matmul 对象，使其在 Kernel 中可用。
