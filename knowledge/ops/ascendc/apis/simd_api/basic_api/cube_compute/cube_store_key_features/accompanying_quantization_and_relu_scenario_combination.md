---
type: API
title: 随路量化与随路ReLU场景组合
description: 矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 随路量化与随路ReLU场景组合

矩阵搬出支持随路量化与随路 ReLU 的组合。M1 为原始数据正数时使用的系数，M2 为负数时使用的系数。NPU 架构版本 2201：M1/M2 取 QUANT_PRE[31:0]（scalar）或 Quant_PRE_ADDR[i][31:0]（tensor），i 为列索引。NPU 架构版本 3510（950）：M1/M2 取 QUANT_PRE[31:13] 或 Quant_PRE_ADDR[i][31:13]。

组合规则：no ReLU 时 M1=M2=量化参数；Normal ReLU 时 M1=量化参数、M2=0。支持的 quantPre 模式含 REQ8/DEQF16/QF322B8_PRE（scalar）及 VREQ8/VDEQF16/VQF322B8_PRE（tensor），3510 额外支持 FP8/HIF8/BF16/F32 等扩展模式。

<!-- cannbot:related:start -->
## 相关

- [通过FP Buffer存放量化参数实现高效随路量化](../../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/fp_buffer_quantization.md)（`explains`）：量化与 ReLU 组合卡说明在同一次 Fixpipe 中叠加后处理时的合法配置。
- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：随路量化与随路ReLU场景组合说明矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。
- [AscMulAddRelu](../../../c_api/vector_compute/asc_mul_add_relu.md)（`related`）：AscMulAddRelu 与《随路量化与随路ReLU场景组合》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 与《随路量化与随路ReLU场景组合》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L1与Fixpipe Buffer数据搬运](../../data_move_guide/l1_fixpipe_data_move.md)（`related`）：组合场景说明量化与 ReLU 参数如何被 Fixpipe 消费，补足 L1-Fixpipe 搬运之后的执行语义。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《随路量化与随路ReLU场景组合》说明矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：SetFixPipeClipRelu 配置 clip-ReLU 路径，可补全组合场景的裁剪激活配置，但仅适用于其正文限定的平台和模式。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 写入组合场景所需的量化张量参数，是随路量化在 Store 流水中的配置入口。
- [矩阵搬出关键特性说明](cube_store_key_features.md)（`related`）：Cube Store 关键特性总览把随路量化、随路 ReLU 与组合场景置于同一输出流水中。
- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`related`）：矩阵搬出寄存器配置说明 与《随路量化与随路ReLU场景组合》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [AccompanyingQuantization](accompanying_quantization.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“随路量化与随路ReLU场景组合”明确矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [AscGetL0c2gmRelu](../../../c_api/cube_compute/asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《随路量化与随路ReLU场景组合》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [随路ReLU](accompanying_relu.md)（`same_topic`）：随路量化与 ReLU 组合页给出 M1/M2 在 no ReLU、Normal ReLU 及不同 quantPre 模式下的取值，是随路 ReLU 与量化同时开启时的约束矩阵。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`same_topic`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《随路量化与随路ReLU场景组合》具体提供“矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
<!-- cannbot:related:end -->
