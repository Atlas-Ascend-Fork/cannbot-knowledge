---
type: API
title: SetFixPipeClipRelu
description: 在L0C Buffer到GM搬运随路量化后，设置ClipReLU操作的最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeClipRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# SetFixPipeClipRelu

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。

参数：config 为 uint64_t 类型，表示 ClipReLU 的最大值 clipReluMaxVal。仅 Atlas 200I/500 A2 推理产品和 Kirin X90/9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../cube_compute_load/data_copy_l1_to_fixpipe.md)（`related`）：ClipReLU 参数需先从 L1 搬入 Fixpipe Buffer，DataCopyL1ToFixpipe 是该配置数据的传输入口。
- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：SetFixPipeClipRelu 的效果发生在 Fixpipe 将 L0C 结果搬到 GM 的阶段，二者构成配置与执行关系。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 与《SetFixPipeClipRelu》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L1与Fixpipe Buffer数据搬运](../../data_move_guide/l1_fixpipe_data_move.md)（`related`）：指南指出该通路用于搬运随路 ReLU 参数，SetFixPipeClipRelu 正是参数进入 Fixpipe 后的消费配置。
- [随路ReLU](../cube_store_key_features/accompanying_relu.md)（`related`）：开启 reluPre 与 clipReluPre 后必须调用 SetFixPipeClipRelu 设置 clipReluMaxVal，该接口完成随路 ClipReLU 的上界配置。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《SetFixPipeClipRelu》具体提供“在L0C Buffer到GM搬运随路量化后，设置ClipReLU操作的最大值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [随路量化与随路ReLU场景组合](../cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：SetFixPipeClipRelu 配置 clip-ReLU 路径，可补全组合场景的裁剪激活配置，但仅适用于其正文限定的平台和模式。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixPipeClipRelu》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [SetFixPipeConfig](set_fix_pipe_config.md)（`same_topic`）：SetFixPipeConfig 与《SetFixPipeClipRelu》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [矩阵搬出寄存器配置说明](cube_store_aux_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeClipRelu》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
<!-- cannbot:related:end -->
