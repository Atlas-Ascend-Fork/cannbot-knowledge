---
type: API
title: DataCopy
description: 将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_ND2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（GM到L1 ND2NZ格式转换）

将Global Memory中的ND格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的NZ格式）、srcTensor（GM源ND格式）、dataCopyParams（搬运参数含源/目的shape等）。约束：遵循Cube计算格式转换和地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AIV核上的ND2NZ格式转换](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：AIV 预转置方案针对内轴不满足 256B 时 GM→L1 随路 ND2NZ 带宽偏低；该 DataCopy 卡正是被替换的随路转换基线。
- [DataCopy](data_copy_gm_to_l1_continuous.md)（`related`）：连续 ND 搬运与 ND→NZ 格式转换按目标布局选用。
- [DataCopyPad（GMToL1非对齐数据搬运）](data_copy_pad_gm_to_l1.md)（`related`）：《DataCopy》明确“将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [CopyGmToL1](../../cube_compute_tensor_api/cube_compute_load/copy_gm_to_l1.md)（`same_topic`）：DataCopy 的核心契约是“将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换”；CopyGmToL1 补充“通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入”。
- [DataCopy](data_copy_gm_to_l1_dn2_nz.md)（`same_topic`）：DataCopy 的核心契约是“将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换”；DataCopy 补充“随路格式转换数据搬运，将数据从Global Memory搬运至L1 Buffer（TPosition为A1/B1），搬运过程中完成DN到NZ格式转换”。
<!-- cannbot:related:end -->
