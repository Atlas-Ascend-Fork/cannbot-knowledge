---
type: API
title: FixpipeL0CToGM
description: 将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# FixpipeL0CToGM

Fixpipe 是 L0C Buffer→Global Memory 的组合搬出接口，内部封装寄存器设置与数据搬运，相比 DataCopy 减少显式调用 Set* 接口。头文件 `basic_api/kernel_operator_fixpipe_intf.h`、`basic_api/kernel_operator_data_copy_intf.h`。

支持随路 scalar/tensor 量化（QuantMode_t）、ReLU、NZ2ND/NZ2NZ/NZ2DN 格式转换和通道切分。按平台使用不同参数结构体：FixpipeParamsArch3510（950，支持 FP8/HIF8 等扩展量化模式）、FixpipeParamsV220（a2/a3）、FixpipeParamsM300（Atlas 200I/500 A2）。模板 config 取 CFG_ROW_MAJOR(NZ2ND)、CFG_NZ(NZ2NZ)、CFG_COLUMN_MAJOR(NZ2DN，仅 950)。

参数：dst 为 GlobalTensor（ND 1B/NZ 32B 对齐）；src 为 LocalTensor（L0C，NZ 64B 对齐）；intriParams 为对应平台参数；cbufWorkspace 为 tensor 量化参数（L1，32B 对齐，quantPre 为 VDEQF16/VQF322B8_PRE/VREQ8 时使用）。关键字段：nSize[0,4095]须 16 倍数（channelSplit 时 8 倍数）、mSize[0,65535]（NZ2ND 时 [0,8192]）、srcStride、dstStride、quantPre、deqScalar、reluEn、unitFlag(0/2/3)、ndNum/srcNdStride/dstNdStride（多 ND 矩阵）。

约束：mSize/nSize/ndNum 为 0 时 NOP；量化参数不能为 inf/nan/非规格化数；float32 尾数 10bits，golden 需清零低 13bits；channelSplit 不能与 NZ2ND/NZ2DN 同时开启。支持 950/a2/a3/Kirin X90/9030。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《FixpipeL0CToGM》补充：将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_ub_to_gm_nz2_nd.md)（`related`）：DataCopy 与《FixpipeL0CToGM》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [DataCopyL0CToGM](data_copy_l0_c_to_gm.md)（`related`）：FixpipeL0CToGM 封装寄存器设置与搬运，DataCopyL0CToGM 则需调用方显式设置随路量化/格式转换寄存器；二者服务同一搬出但控制方式不同。
- [FixpipeL0CToL1](fixpipe_l0_c_to_l1.md)（`related`）：FixpipeL0CToGM 与本卡共享量化、ReLU、格式转换机制，但目的存储从 L1 改为 GM，可用于按后续消费者位置选择搬出通路。
- [FixpipeL0CToUB](fixpipe_l0_c_to_ub.md)（`related`）：L0C→GM 与 L0C→UB Fixpipe 分别支持 GM 中转和 UB 直通融合数据流，目的层级决定后续 AIV 路径。
- [L0C Buffer内存结构介绍](l0_c_memory_structure_intro.md)（`related`）：Fixpipe 从 L0C 读取 NZ/Bank 布局并转换后写 GM，理解 bank 行宽是配置 m/n/stride 的前提。
- [NZ2DN](../cube_store_key_features/nz2_dn.md)（`related`）：FixpipeL0CToGM说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。
- [NZ2NZ](../cube_store_key_features/nz2_nz.md)（`related`）：FixpipeL0CToGM 通过 CFG_NZ 或关闭转换 flag 执行 NZ2NZ 搬出。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《FixpipeL0CToGM》说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：SetFixPipeClipRelu 的效果发生在 Fixpipe 将 L0C 结果搬到 GM 的阶段，二者构成配置与执行关系。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《FixpipeL0CToGM》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [SetFixpipeNz2ndFlag](../cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《FixpipeL0CToGM》说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`related`）：该参数在 Fixpipe 将 L0C 结果搬到 GM 时生效，二者构成参数设置与数据搬出的上下游。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《FixpipeL0CToGM》具体提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToGM》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [UnitFlag](../../cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《FixpipeL0CToGM》提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
