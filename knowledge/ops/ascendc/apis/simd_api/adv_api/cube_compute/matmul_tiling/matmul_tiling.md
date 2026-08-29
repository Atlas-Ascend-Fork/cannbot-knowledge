---
type: API
title: Matmul Tiling类
description: 提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/Matmul_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul Tiling类

提供矩阵乘计算的 Host 侧 Tiling 类，通过 TCubeTiling 结构体承载切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetAType/SetBType/SetCType/SetBiasType 设置各矩阵数据类型，SetSingleShape/SetShape/SetOrgShape 设置形状参数，SetALayout/SetBLayout/SetCLayout 设置排布格式。
切分控制方法包括 SetFixSplit、EnableMultiCoreSplitK、SetSplitK、SetSplitRange、SetDoubleBuffer 等；GetBaseM/GetBaseN/GetBaseK 查询基础分块大小，GetCoreNum 查询核数。
另支持 EnableBias、SetMadType、SetDequantType、SetSparse 等特性开关。
