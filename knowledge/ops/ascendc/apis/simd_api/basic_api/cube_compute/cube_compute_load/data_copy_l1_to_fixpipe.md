---
type: API
title: DataCopy
description: 将随路量化参数从L1 Buffer搬运到Fixpipe Buffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_L1ToFixpipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（L1到Fixpipe搬运）

将L1 Buffer中的数据搬运到Fixpipe，用于Cube计算中Fixpipe数据处理。

函数原型通过模板参数指定数据类型。参数包含dstTensor（Fixpipe目的）、srcTensor（L1源）、dataCopyParams（搬运参数）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：ClipReLU 参数需先从 L1 搬入 Fixpipe Buffer，DataCopyL1ToFixpipe 是该配置数据的传输入口。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《DataCopy》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：两者都把 L1 中的量化参数搬到 Fixpipe；Tensor Copy 由 Layout 推导参数，ISASI DataCopy 显式传 dataCopyParams。
- [L1与Fixpipe Buffer数据搬运](../../data_move_guide/l1_fixpipe_data_move.md)（`same_topic`）：指南描述的 L1 到 Fixpipe 连续搬运由该 DataCopy 接口直接实现，并共享 32B 与 128B 对齐约束。
<!-- cannbot:related:end -->
