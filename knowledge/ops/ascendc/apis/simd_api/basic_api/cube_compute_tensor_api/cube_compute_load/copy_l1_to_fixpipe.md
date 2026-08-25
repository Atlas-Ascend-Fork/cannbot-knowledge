---
type: API
title: CopyL1ToFixpipe
description: 通过Tensor API的Copy接口将L1 Buffer中的量化数据搬运到Fixpipe Buffer，用于L0C输出时随路量化。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToFixpipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到Fixpipe数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到Fixpipe，用于矩阵计算中Fixpipe数据处理。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [Copy](../cube_compute_store/copy_l0_c_to_gm.md)（`related`）：使用 tensor QuantPre 搬出时，量化 tensor 需先从 L1 搬到 Fixpipe；CopyL1ToFixpipe 是 CopyL0CToGM 随路量化的上游参数准备。
- [CopyL1ToBiasTable](copy_l1_to_bias_table.md)（`related`）：BiasTable 和 Fixpipe 是不同辅助 buffer，后续消费单元决定目标。
- [SetFixPipeAddr](../../cube_compute/cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《CopyL1ToFixpipe》说明通过Tensor API的Copy接口将L1 Buffer中的量化数据搬运到Fixpipe Buffer，用于L0C输出时随路量化。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeConfig](../../cube_compute/cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《CopyL1ToFixpipe》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [CopyGmToL1](copy_gm_to_l1.md)（`same_topic`）：CopyL1ToFixpipe 与《CopyGmToL1》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_l1_to_fixpipe.md)（`same_topic`）：两者都把 L1 中的量化参数搬到 Fixpipe；Tensor Copy 由 Layout 推导参数，ISASI DataCopy 显式传 dataCopyParams。
- [FixpipeL0CToGM](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_gm.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToGM》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [FixpipeL0CToL1](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_l1.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToL1》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [FixpipeL0CToUB](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_ub.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToUB》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [L1与Fixpipe Buffer数据搬运](../../data_move_guide/l1_fixpipe_data_move.md)（`same_topic`）：CopyL1ToFixpipe 与《L1与Fixpipe Buffer数据搬运》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [SetFixPipeClipRelu](../../cube_compute/cube_store_aux_config/set_fix_pipe_clip_relu.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixPipeClipRelu》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [SetFixpipeNz2ndFlag](../../cube_compute/cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixpipeNz2ndFlag》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [SetFixpipePreQuantFlag](../../cube_compute/cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixpipePreQuantFlag》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [基础API随路量化](../cube_store_key_features/quant_pre.md)（`same_topic`）：CopyL1ToFixpipe 与《基础API随路量化》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵搬出关键特性说明](../cube_store_key_features/cube_store_key_features.md)（`same_topic`）：CopyL1ToFixpipe 与《矩阵搬出关键特性说明》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《CopyL1ToFixpipe》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：CopyL1ToFixpipe 与《矩阵计算的搬出》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵计算的搬出总体说明](../cube_compute_store/overall_description.md)（`same_topic`）：CopyL1ToFixpipe 与《矩阵计算的搬出总体说明》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
<!-- cannbot:related:end -->
