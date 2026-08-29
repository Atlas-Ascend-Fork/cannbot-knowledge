---
type: API
title: SetFixpipePreQuantFlag
description: DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置scalar量化参数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixpipePreQuantFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFixpipePreQuantFlag

DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。

参数：config 为 uint64_t 类型，表示 scalar 量化参数。支持 950/a2/a3/Atlas 200I/500 A2/Kirin X90/9030，不支持 Atlas 推理 AI Core/Vector Core/Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。；矩阵搬出过程中支持随路 cast 和 quant 能力。Cast 模式（CAST_RINT）：L0C float 输出 half 配 F322F16，输出 bfloat16_t 配 F322BF16，无需额外寄存器。Quant 模式分两种：Scalar 量化（整个 C 矩阵一个参数，shape［1］，通过 SetFixpipePreQuantFlag 设置 QUANT_PRE，uint64_t 低 32 位 float（1,8,10 格式））；Tensor 量化（每列一个参数，shape［n］，通过 SetFixPipeConfig 设置 Quant_PRE_ADDR，需从 L1 搬运至 Fixpipe Buffer）。。配置接口写入整个矩阵共用的 scalar 量化参数，特性卡明确该参数属于 Scalar 随路量化模式。
- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。；数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。SetFixpipePreQuantFlag 产生量化寄存器配置，L0C 到 GM 的 DataCopy 在对应量化模式中消费该配置。
- [DataCopyL0CToL1](../cube_compute_store/data_copy_l0_c_to_l1.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。F322F16/F322BF16 为 Cast 模式，DEQF16/VDEQF16/REQ8/VREQ8 等为 scalar/tensor 量化，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”把 REQ8/VREQ8 等 scalar 量化列为需要预置寄存器的模式；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。”说明 SetFixpipePreQuantFlag 设置的是全输出矩阵共享参数。组合后可避免把 scalar 配置误当 tensor 配置。
<!-- cannbot:related:end -->
