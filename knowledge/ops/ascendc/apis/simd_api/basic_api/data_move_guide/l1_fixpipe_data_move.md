---
type: API
title: L1与Fixpipe Buffer数据搬运
description: DataCopy能够实现L1 Buffer至Fixpipe Buffer的连续数据搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_Fixpipe_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1与Fixpipe Buffer数据搬运

DataCopy 实现 L1 Buffer 到 Fixpipe Buffer 的连续数据搬运，格式和内容保持不变。用于将随路量化和随路 ReLU 参数从 L1 搬运至 Fixpipe Buffer。Fixpipe Buffer 地址需 128B 对齐，L1 Buffer 地址需 32B 对齐。

<!-- cannbot:related:start -->
## 相关

- [SetFixPipeClipRelu](../cube_compute/cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：指南指出该通路用于搬运随路 ReLU 参数，SetFixPipeClipRelu 正是参数进入 Fixpipe 后的消费配置。
- [数据搬运导览](data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《L1与Fixpipe Buffer数据搬运》说明DataCopy能够实现L1 Buffer至Fixpipe Buffer的连续数据搬运，数据搬运时格式和内容保持不变。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [随路量化与随路ReLU场景组合](../cube_compute/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：组合场景说明量化与 ReLU 参数如何被 Fixpipe 消费，补足 L1-Fixpipe 搬运之后的执行语义。
- [CopyL1ToFixpipe](../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《L1与Fixpipe Buffer数据搬运》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [DataCopy](../cube_compute/cube_compute_load/data_copy_l1_to_fixpipe.md)（`same_topic`）：指南描述的 L1 到 Fixpipe 连续搬运由该 DataCopy 接口直接实现，并共享 32B 与 128B 对齐约束。
<!-- cannbot:related:end -->
