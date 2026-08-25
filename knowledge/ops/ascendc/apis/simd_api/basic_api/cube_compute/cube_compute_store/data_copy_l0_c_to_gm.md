---
type: API
title: DataCopyL0CToGM
description: 将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopyL0CToGM

将 L0C Buffer（CO1）中 Mmad 计算结果搬运至 Global Memory，支持随路量化、ReLU 激活、NZ2ND 格式转换和通道切分。头文件 `basic_api/kernel_operator_data_copy_intf.h`。

参数：dst 为 GlobalTensor（ND 1 字节对齐 / NZ 32 字节对齐）；src 为 LocalTensor（L0C，NZ 格式 64 字节对齐）；intriParams 为 DataCopyCO12DstParams。关键字段：nSize[0,4095]须为 16 倍数，mSize[0,65535]（开启 NZ2ND 时 [0,8192]），dstStride、srcStride、unitFlag(0/2/3)、quantPre(QuantMode_t)、reluPre(0/1)、channelSplit(bool)、nz2ndEn(bool)。

数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。

约束：mSize 或 nSize 为 0 时为 NOP；量化和 ReLU 参数不能为 inf/nan/非规格化数；float32 尾数位为 10bits（非标准 IEEE 754），golden 数据生成需将量化参数低 13bits 清零。支持 950/a2/a3，不支持 Atlas 推理/训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：DataCopyL0CToGM说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。
- [Copy](../../cube_compute_tensor_api/cube_compute_store/copy_l0_c_to_gm.md)（`related`）：两接口都把 L0C 结果搬到 GM 并支持格式转换、量化和 ReLU；TensorAPI Copy 自动由 Layout 推导参数，ISASI DataCopy 显式配置 DataCopyCO12DstParams。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_ub_to_gm_nz2_nd.md)（`related`）：DataCopy 与《DataCopyL0CToGM》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [FixpipeL0CToGM](fixpipe_l0_c_to_gm.md)（`related`）：FixpipeL0CToGM 封装寄存器设置与搬运，DataCopyL0CToGM 则需调用方显式设置随路量化/格式转换寄存器；二者服务同一搬出但控制方式不同。
- [L0C Buffer内存结构介绍](l0_c_memory_structure_intro.md)（`related`）：L0C 的 bank/行宽和地址编码决定 DataCopyL0CToGM 的源布局、对齐和 stride 解释。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《DataCopyL0CToGM》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [基础API随路量化](../../cube_compute_tensor_api/cube_store_key_features/quant_pre.md)（`related`）：《DataCopyL0CToGM》明确“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。”；它与《基础API随路量化》的“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。”在实际调用参数、数据流或结果校验上直接衔接。
- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“DataCopyL0CToGM”明确将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [UnitFlag](../../cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《DataCopyL0CToGM》提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
