---
type: API
title: DataCopy
description: 将数据从Unified Buffer搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_UBToL1_ND2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（UB到L1 ND2NZ格式转换）

将Unified Buffer中的ND格式数据搬运到L1 Buffer并转换为NZ格式。用于从Vector侧向Cube侧传递数据时的随路格式转换。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的NZ格式）、srcTensor（UB源ND格式）、dataCopyParams。约束：遵循Cube计算格式转换约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_ub_to_l1_highdim_split.md)（`related`）：《DataCopy》明确“将数据从Unified Buffer搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
