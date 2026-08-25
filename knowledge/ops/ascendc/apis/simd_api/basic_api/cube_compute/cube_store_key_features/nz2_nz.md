---
type: API
title: NZ2NZ
description: 矩阵计算的搬出过程中NZ2NZ的核心功能体现为，矩阵计算结果搬出前后保持NZ数据排布不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2NZ

矩阵搬出时保持 NZ 数据排布不变，不进行格式转换。通过 Fixpipe/DataCopy 的 config=CFG_NZ 或不开启 NZ2ND/NZ2DN 时默认使用。

参数：mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵不同 Z 分形列间隔（单位 C0_Size=16×sizeof(T)）、dstStride 为目的 NZ 矩阵不同 Z 分形列间隔。a2/a3：dstStride 单位为 datablock(32B)；950（FixpipeParamsArch3510）：dstStride 单位为 element。支持 a2/a3 和 950。
