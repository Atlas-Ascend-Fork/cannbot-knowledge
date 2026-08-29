---
type: API
title: 矩阵计算分形介绍
description: 矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_fractal_intro/cube_compute_fractal_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算分形介绍

矩阵计算单元采用 16×16 分块计算，传统线性存储在读取矩形数据块时需访问不连续地址，效率低。分形存储格式通过软件重排使每个 16×16 计算块在物理内存中连续存放，硬件一次连续读取即可加载整个数据块。

文档采用"大Y小x"命名法：大Y（Z/N）表示分形矩阵间排列顺序（Z 行主序、N 列主序），小x（z/n）表示分形矩阵内部元素排列顺序。矩阵乘法 A×B=C 的格式组合：多数产品使用 Zz×Zn=Nz，Ascend 950PR/950DT 使用 Nz×Zn=Nz。常见格式包括 ND（线性连续）、Nz、Zz、Zn，以及 NC1HWC0 等。
