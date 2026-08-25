---
type: API
title: NZ2ND
description: 矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2ND.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2ND

矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。

参数：ndNum 为 ND 矩阵个数、mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵不同 Z 分形列间隔（单位 C0_Size）、dstStride 为目的 ND 矩阵不同行间隔（单位 element）、srcNdStride 为不同 NZ 矩阵间隔（单位 16×C0_Size）、dstNdStride 为不同 ND 矩阵间隔（单位 element）。约束：不能与 Channel Split/Merge 同时开启；目标操作数地址不能重叠。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《NZ2ND》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《NZ2ND》补充：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。
- [AscSetMmadDirectionN](../../../c_api/cube_compute/asc_set_mmad_direction_n.md)（`related`）：DirectionN 的适用场景之一是 UnitFlag 开启且搬出做 NZ2ND，二者顺序需匹配。
- [GmUbDataMove](../../data_move_guide/gm_ub_data_move.md)（`related`）：GmUbDataMove 与《NZ2ND》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NZ2NZ](nz2_nz.md)（`related`）：NZ2ND 在搬出时把分形 NZ 转为普通 ND；与保持 NZ 的 focal 是直接格式选型。
- [SetFixpipeNz2ndFlag](../cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“SetFixpipeNz2ndFlag”定义：DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [SetMMColumnMajor/SetMMRowMajor](../mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《NZ2ND》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [Transpose](../../../adv_api/tensor_transform/transpose.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NZ2ND》明确提供“矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [卷积格式转换](convolution_format_conversion.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“卷积格式转换”定义：在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [矩阵搬出关键特性说明](cube_store_key_features.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“矩阵搬出关键特性说明”定义：矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`related`）：矩阵搬出寄存器配置说明 与《NZ2ND》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [AscSetL0c2gmNz2nd](../../../c_api/cube_compute/asc_set_l0c2gm_nz2nd.md)（`same_topic`）：AscSetL0c2gmNz2nd 与《NZ2ND》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_ub_to_gm_nz2_nd.md)（`same_topic`）：DataCopy 与《NZ2ND》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
<!-- cannbot:related:end -->
