---
type: API
title: SetSparse
description: 设置Matmul的使用场景是否为Sparse Matmul场景。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSparse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSparse

设置Matmul的使用场景是否为Sparse Matmul场景。

参数：
- isSparseIn（输入）：设置是否为Sparse Matmul稀疏场景。 true：稀疏场景。 false：非稀疏场景。

返回值：-1表示设置失败；0表示设置成功。
