---
type: API
title: SetFixPipeConfig
description: DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFixPipeConfig

DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。有两个重载：传入 reluPre 和 quantPre 两个 tensor，或传入 preData 一个 tensor（模板 setRelu 当前仅支持 false，即只设置 quantPre）。

参数：reluPre 为 ReLU tensor（Fixpipe Buffer/C2PIPE2GM，当前保留，传空 LocalTensor）；quantPre 为 quant tensor（Fixpipe Buffer，uint64_t）；preData 为单个 tensor（当前仅支持 quant tensor）；isUnitFlag 为 bool，true 时清空 L0C Buffer 所有内存块的 unitFlag 标志位。约束：quantPre 和 reluPre 必须在 Fixpipe Buffer 上。支持 950/a2/a3/Atlas 200I/500 A2/Kirin X90/9030。

<!-- cannbot:related:start -->
## 相关

- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`related`）：SetFixPipeConfig 与《AccompanyingQuantization》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [AscSetL0c2gmConfig](../../../c_api/cube_compute/asc_set_l0c2gm_config.md)（`related`）：SetFixPipeConfig 与《AscSetL0c2gmConfig》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`related`）：SetFixPipeConfig 与《CopyL1ToFixpipe》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [DataCopy](../cube_compute_load/data_copy_l1_to_fixpipe.md)（`related`）：SetFixPipeConfig 与《DataCopy》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：SetFixPipeConfig 与《DataCopyL0CToGM》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [DataCopyL0CToL1](../cube_compute_store/data_copy_l0_c_to_l1.md)（`related`）：SetFixPipeConfig 与《DataCopyL0CToL1》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：SetFixPipeConfig 与《FixpipeL0CToGM》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [FixpipeL0CToL1](../cube_compute_store/fixpipe_l0_c_to_l1.md)（`related`）：SetFixPipeConfig 与《FixpipeL0CToL1》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [SetFixpipeNz2ndFlag](set_fixpipe_nz2nd_flag.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《SetFixPipeConfig》说明DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [SetFixpipePreQuantFlag](set_fixpipe_pre_quant_flag.md)（`related`）：SetFixpipePreQuantFlag 提供 scalar 量化参数，SetFixPipeConfig 把量化配置组织到 L0C 搬出路径。
- [SetMMColumnMajor/SetMMRowMajor](../mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《SetFixPipeConfig》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [UnitFlag](../mmad_compute_key_features/unit_flag.md)（`related`）：SetFixPipeConfig 与《UnitFlag》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [基础API随路量化](../../cube_compute_tensor_api/cube_store_key_features/quant_pre.md)（`related`）：SetFixPipeConfig 与《基础API随路量化》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [随路ReLU](../cube_store_key_features/accompanying_relu.md)（`related`）：SetFixPipeConfig 与《随路ReLU》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《SetFixPipeConfig》具体提供“DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [随路量化与随路ReLU场景组合](../cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：SetFixPipeConfig 写入组合场景所需的量化张量参数，是随路量化在 Store 流水中的配置入口。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`same_topic`）：FixpipeL0CToUB 与《SetFixPipeConfig》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [SetFixPipeAddr](set_fix_pipe_addr.md)（`same_topic`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《SetFixPipeConfig》说明DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeClipRelu](set_fix_pipe_clip_relu.md)（`same_topic`）：SetFixPipeConfig 与《SetFixPipeClipRelu》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [UnitFlag](../../cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《SetFixPipeConfig》提供“DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [矩阵搬出寄存器配置说明](cube_store_aux_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeConfig》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
<!-- cannbot:related:end -->
