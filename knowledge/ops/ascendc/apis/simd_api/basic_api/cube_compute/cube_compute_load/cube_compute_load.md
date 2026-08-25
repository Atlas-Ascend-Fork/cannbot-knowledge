---
type: API
title: 矩阵计算的搬入
description: 矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/cube_compute_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算的搬入

矩阵计算 ISASI 搬入接口集，提供 GM/L1/L0A/L0B 之间矩阵数据搬运的底层接口。
LoadData 系列支持 2D 矩阵搬运（含 V2、MX、BitMode 变体）、卷积数据搬运、带转置/稀疏/Stride 的搬运；DataCopy 系列支持 GM/L1 与 UB 间连续、高维切分及非对齐搬运，并支持 DN2NZ/ND2NZ 随路格式转换。
另提供 BroadCastVecToMM 向量到矩阵广播、DataCopy(L1ToBiasTable/Fixpipe) 等专用搬运接口，以及 L1-L0A/L0B 内存结构与输入搬运约束说明。
使用前需了解各接口的路径约束与内存对齐要求。
