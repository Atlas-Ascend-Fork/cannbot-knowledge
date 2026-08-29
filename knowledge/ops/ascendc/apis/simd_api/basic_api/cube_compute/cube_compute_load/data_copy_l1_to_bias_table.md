---
type: API
title: DataCopy
description: 将矩阵计算用到的Bias参数从L1 Buffer搬运到BiasTable Buffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_L1ToBiasTable.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（L1到BiasTable搬运）

将L1 Buffer中的bias数据搬运到BiasTable，用于Mmad计算的bias输入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（BiasTable目的）、srcTensor（L1源）、dataCopyParams（搬运参数）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [L1与BiasTable Buffer数据搬运](../../data_move_guide/l1_bias_table_data_move.md)（`same_topic`）：“将L1 Buffer中的bias数据搬运到BiasTable，用于Mmad计算的bias输入。”；“DataCopy 实现 L1 Buffer 到 BiasTable Buffer 的连续数据搬运，格式和内容保持不变。”。目标页给出焦点 API 的连续搬运语义和不变性。
<!-- cannbot:related:end -->
