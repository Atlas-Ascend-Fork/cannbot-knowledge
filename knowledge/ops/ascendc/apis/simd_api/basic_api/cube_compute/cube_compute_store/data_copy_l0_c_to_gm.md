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

- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`related`）：矩阵搬出过程中支持随路 cast 和 quant 能力。Cast 模式（CAST_RINT）：L0C float 输出 half 配 F322F16，输出 bfloat16_t 配 F322BF16，无需额外寄存器。Quant 模式分两种：Scalar 量化（整个 C 矩阵一个参数，shape［1］，通过 SetFixpipePreQuantFlag 设置 QUANT_PRE，uint64_t 低 32 位 float（1,8,10 格式））；Tensor 量化（每列一个参数，shape［n］，通过 SetFixPipeConfig 设置 Quant_PRE_ADDR，需从 L1 搬运至 Fixpipe Buffer）。；数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。特性卡定义矩阵搬出的随路 cast/quant，L0C 到 GM 的 DataCopy 卡给出可达模式及必须配套的量化寄存器。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 Elementwise 操作时 LocalTensor 的地址。；量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。SetFixPipeAddr 配置 L0C 到 GM 随路量化的 Elementwise 地址，DataCopyL0CToGM 是明确消费该配置的搬运接口。
- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。；量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。SetFixPipeClipRelu 写入 L0C→GM 随路 ClipReLU 上限，DataCopyL0CToGM 明确在受支持平台消费该附加配置。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”把 tensor 量化模式的寄存器前置配置列为必需步骤；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。”定义 SetFixPipeConfig 正是 L0C→GM tensor 量化参数的生产接口。该边直接支撑量化 DataCopy 的正确调用顺序。
- [SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。；数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。SetFixpipePreQuantFlag 产生量化寄存器配置，L0C 到 GM 的 DataCopy 在对应量化模式中消费该配置。
<!-- cannbot:related:end -->
