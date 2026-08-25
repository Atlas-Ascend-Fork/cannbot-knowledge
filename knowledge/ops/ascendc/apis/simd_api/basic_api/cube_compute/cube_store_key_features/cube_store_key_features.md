---
type: API
title: 矩阵搬出关键特性说明
description: 矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/cube_store_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出关键特性说明

矩阵计算 ISASI 搬出阶段支持的关键后处理特性，在 L0C 到 GM/UB/L1 搬运过程中随路完成。
格式转换方面支持 NZ2ND、NZ2NZ、NZ2DN 等排布格式变换；通道处理方面支持 Int8 Channel Merge 和 F32 Channel Split 通道合并与拆分。
随路计算方面支持随路量化与随路 ReLU，并支持两者场景组合；另支持 L0C 到 UB 双目标模式和卷积格式转换等特性。

<!-- cannbot:related:start -->
## 相关

- [NZ2ND](nz2_nd.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“矩阵搬出关键特性说明”定义：矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [SetFixpipeNz2ndFlag](../cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《矩阵搬出关键特性说明》说明矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [矩阵搬出关键特性说明](../../cube_compute_tensor_api/cube_store_key_features/cube_store_key_features.md)（`related`）：TensorAPI 的矩阵搬出特性与 ISASI 卡覆盖相同的 NZ 转换、通道拆并和随路量化/ReLU，但面向不同编程接口。
- [随路ReLU](accompanying_relu.md)（`related`）：ISASI 矩阵搬出关键特性页把随路 ReLU 定位在 L0C 到 GM/UB/L1 的 FixPipe 后处理链，并关联格式转换、通道处理和量化。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出关键特性说明》具体提供“矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [随路量化与随路ReLU场景组合](accompanying_quantization_and_relu_scenario_combination.md)（`related`）：Cube Store 关键特性总览把随路量化、随路 ReLU 与组合场景置于同一输出流水中。
- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《矩阵搬出关键特性说明》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵搬出关键特性说明》明确“矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
