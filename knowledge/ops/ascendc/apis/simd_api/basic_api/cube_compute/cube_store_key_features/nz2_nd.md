---
type: API
title: NZ2ND
description: 矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2ND.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2ND

矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。

参数：ndNum 为 ND 矩阵个数、mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵不同 Z 分形列间隔（单位 C0_Size）、dstStride 为目的 ND 矩阵不同行间隔（单位 element）、srcNdStride 为不同 NZ 矩阵间隔（单位 16×C0_Size）、dstNdStride 为不同 ND 矩阵间隔（单位 element）。约束：不能与 Channel Split/Merge 同时开启；目标操作数地址不能重叠。
