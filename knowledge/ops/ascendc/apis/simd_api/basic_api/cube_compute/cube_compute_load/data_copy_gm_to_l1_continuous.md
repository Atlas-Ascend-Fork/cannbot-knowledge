---
type: API
title: DataCopy
description: 将矩阵从Global Memory连续搬运至L1 Buffer（TPosition为A1/B1），数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（GM到L1连续搬运）

将Global Memory中的连续数据搬运到L1 Buffer，数据格式不变。用于矩阵计算输入的连续数据搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的）、srcTensor（GM源）、dataCopyParams（搬运参数含shape/stride等）。约束：源/目的地址需满足对齐要求；遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_to_l1_highdim_split.md)（`related`）：高维切分需显式 stride/repeat，不能伪装线性连续。
- [DataCopy](data_copy_gm_to_l1_nd2_nz.md)（`related`）：连续 ND 搬运与 ND→NZ 格式转换按目标布局选用。
- [DataCopyPad（GMToL1非对齐数据搬运）](data_copy_pad_gm_to_l1.md)（`related`）：非对齐尾块需 Pad 版本，普通 continuous 不隐式补齐。
- [CopyGmToL1](../../cube_compute_tensor_api/cube_compute_load/copy_gm_to_l1.md)（`same_topic`）：Tensor API 提供同一 GM→L1 连续搬运。
<!-- cannbot:related:end -->
