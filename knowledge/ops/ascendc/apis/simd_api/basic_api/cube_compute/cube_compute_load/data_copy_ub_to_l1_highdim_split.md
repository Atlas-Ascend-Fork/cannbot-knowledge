---
type: API
title: DataCopy
description: 将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_UBToL1_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（UB到L1高维切分搬运）

将Unified Buffer中的高维数据按切分策略搬运到L1 Buffer，支持多段搬运。用于高维数据的分块搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams（含切分和步长信息）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_to_l1_highdim_split.md)（`related`）：《DataCopy》明确“将矩阵从Global Memory搬运至L1 Buffer，支持通过配置数据块个数、长度和地址偏移实现高维切分的非连续搬运，搬运时格式和内容保持不变。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopy](data_copy_ub_to_l1_continuous.md)（`related`）：两者数据路径同为 UB 到 L1；连续版用于一段连续矩阵，高维切分版增加分段与 stride 描述，提供按布局选择搬运重载的边界。
- [DataCopy](data_copy_ub_to_l1_nd2_nz.md)（`related`）：《DataCopy》明确“将数据从Unified Buffer搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_ub_to_ub_highdim_split.md)（`related`）：《DataCopy》明确“支持UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
