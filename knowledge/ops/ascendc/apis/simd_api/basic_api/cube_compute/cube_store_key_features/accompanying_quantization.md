---
type: API
title: AccompanyingQuantization
description: 矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/accompanying_quantization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AccompanyingQuantization

矩阵搬出过程中支持随路 cast 和 quant 能力。Cast 模式（CAST_RINT）：L0C float 输出 half 配 F322F16，输出 bfloat16_t 配 F322BF16，无需额外寄存器。Quant 模式分两种：Scalar 量化（整个 C 矩阵一个参数，shape[1]，通过 SetFixpipePreQuantFlag 设置 QUANT_PRE，uint64_t 低 32 位 float（1,8,10 格式））；Tensor 量化（每列一个参数，shape[n]，通过 SetFixPipeConfig 设置 Quant_PRE_ADDR，需从 L1 搬运至 Fixpipe Buffer）。

通用量化模式：DEQF16/VDEQF16（int32→half）、QF322B8_PRE/VQF322B8_PRE（float→int8/uint8）、REQ8/VREQ8（int32→int8/uint8 重量化）。Ascend 950PR/950DT 额外支持 FP8、HIF8（含 Hybrid Round）、QS322BF16、QF322F16/BF16/F32_PRE 等扩展模式。量化算法细节参见随路量化与随路ReLU场景组合。

<!-- cannbot:related:start -->
## 相关

- [通过FP Buffer存放量化参数实现高效随路量化](../../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/fp_buffer_quantization.md)（`explains`）：AccompanyingQuantization 定义 Fixpipe 随路量化的参数和搬出能力，指南给出把参数放入 FP Buffer 的高效实现。
- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：AccompanyingQuantization说明矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《AccompanyingQuantization》说明矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《AccompanyingQuantization》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`related`）：矩阵搬出寄存器配置说明 与《AccompanyingQuantization》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [随路ReLU](accompanying_relu.md)（`related`）：AccompanyingQuantization 定义与随路 ReLU 可组合的 scalar/tensor 量化模式，二者共同决定搬出后的 cast、quant 和激活次序。
- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“DataCopyL0CToGM”明确将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [Int8 Channel Merge](int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；AccompanyingQuantization正文说明“矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“SetFixpipePreQuantFlag”明确DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置scalar量化参数。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [基础API随路量化](../../cube_compute_tensor_api/cube_store_key_features/quant_pre.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“基础API随路量化”明确随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [随路量化与随路ReLU场景组合](accompanying_quantization_and_relu_scenario_combination.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“随路量化与随路ReLU场景组合”明确矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
<!-- cannbot:related:end -->
