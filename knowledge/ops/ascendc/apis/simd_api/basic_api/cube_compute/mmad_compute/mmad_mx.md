---
type: API
title: MmadMx
description: 带量化系数的矩阵乘法接口，左右矩阵各有对应量化系数矩阵，实现C=(scaleA⊗A)*(scaleB⊗B)+Bias。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/MmadMx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MmadMx

Microscaling 矩阵乘加接口，实现 C=(scaleA⊗A)×(scaleB⊗B)+Bias。K 方向每 32 个元素共享一个量化因子。头文件 `basic_api/kernel_operator_mm_intf.h`。

矩阵布局：A（L0A，M×K，Nz）、scaleA（L0A_MX，M×K/32，小z shape(2,16)）、B（L0B，K×N，Zn）、scaleB（L0B_MX，K/32×N，小n shape(2,16)）、C（L0C，M×N，Nz）、Bias（1×N）。支持带/不带 bias 两个原型，mmadParams 为 MmadParams 结构体。仅 Ascend 950PR/950DT 支持。
