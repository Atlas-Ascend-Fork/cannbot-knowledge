---
type: API
title: DataCopy
description: 将矩阵从Global Memory搬运至L1 Buffer，支持通过配置数据块个数、长度和地址偏移实现高维切分的非连续搬运，搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（GM到L1高维切分搬运）

将Global Memory中的高维数据按切分策略搬运到L1 Buffer，支持源/目的侧存在步长时的多段搬运。用于高维矩阵数据的分块搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams（含各维度切分和步长信息）。约束：遵循Cube计算地址对齐和切分约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_to_l1_continuous.md)（`related`）：高维切分需显式 stride/repeat，不能伪装线性连续。
- [DataCopy](data_copy_ub_to_l1_highdim_split.md)（`related`）：《DataCopy》明确“将矩阵从Global Memory搬运至L1 Buffer，支持通过配置数据块个数、长度和地址偏移实现高维切分的非连续搬运，搬运时格式和内容保持不变。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`related`）：高维切分 GM→L1 搬运的各维长度、stride 和分段必须满足 Cube 输入通路的地址对齐、数据长度及格式转换矩阵。
<!-- cannbot:related:end -->
