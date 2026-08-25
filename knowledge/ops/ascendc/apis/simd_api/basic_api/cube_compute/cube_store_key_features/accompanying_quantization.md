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
