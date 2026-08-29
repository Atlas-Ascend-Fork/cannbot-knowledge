---
type: API
title: 数据搬运
description: 矢量数据搬运接口集，涵盖 DataCopy、DataCopyPad、Copy 等 GM/UB 间连续、高维切分、非对齐搬运接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Memory矢量计算数据搬运

- **DataCopy（GM与UB连续数据搬运）**
- **DataCopy（GM与UB高维切分数据搬运）**
- **DataCopy（GM与UB切片数据搬运）**
- **DataCopy（GM -> UB随路转换ND2NZ搬运）**
- **DataCopy（UB -> GM随路转换NZ2ND搬运）**
- **DataCopy（GM -> UB多维数据搬运NDDMA）**
- **DataCopyPad（GM -> UB非对齐数据搬运）**
- **DataCopyPad（UB -> GM非对齐数据搬运）**
- **DataCopy（UB -> UB连续数据搬运）**
- **DataCopy（UB -> UB高维切分数据搬运）**
- **Copy（UB -> UB连续数据搬运）**
- **Copy（UB -> UB掩码式高维数据搬运）**
