---
type: API
title: 矩阵计算的搬出
description: 矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/cube_compute_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算的搬出

矩阵计算 ISASI 搬出接口集，提供 L0C/L1/UB/GM 之间矩阵结果数据的搬运接口。
DataCopy 和 Fixpipe 是两类核心搬运接口，支持 L0C 到 GM、L0C 到 L1、L0C 到 UB 等路径；另提供 DataCopyL1ToUB 和 DataCopy(L1ToGM) 用于 L1 到 UB/GM 的直接搬运。
Fixpipe 支持在搬运过程中执行随路量化与格式转换，具体特性参见矩阵搬出关键特性说明。
