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

<!-- cannbot:related:start -->
## 相关

- [4:2稀疏矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/4_2_sparse_matmul.md)（`explains`）：4:2稀疏矩阵乘 与《SetSparse》的实质衔接是：4:2 稀疏 Matmul 实现直接依赖 SetSparse/SetSparseIndex 和 sparse Mmad 两层接口传递稠密化索引。
- [GetTiling](get_tiling.md)（`related`）：SetSparse 只写入稀疏配置，最终由 GetTiling 消费配置并求解 TCubeTiling；这是设置到求解的直接工作流。
- [MmadWithSparse](../../../basic_api/cube_compute/mmad_compute/mmad_with_sparse.md)（`same_topic`）：SetSparse说明设置Matmul的使用场景是否为Sparse Matmul场景。
- [SetSparseIndex](../matmul_kernel/set_sparse_index.md)（`same_topic`）：SetSparse说明设置Matmul的使用场景是否为Sparse Matmul场景。
<!-- cannbot:related:end -->
