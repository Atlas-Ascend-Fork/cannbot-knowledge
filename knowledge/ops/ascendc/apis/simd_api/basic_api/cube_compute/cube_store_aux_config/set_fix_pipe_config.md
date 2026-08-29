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

- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”把 tensor 量化模式的寄存器前置配置列为必需步骤；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。”定义 SetFixPipeConfig 正是 L0C→GM tensor 量化参数的生产接口。该边直接支撑量化 DataCopy 的正确调用顺序。
- [DataCopyL0CToL1](../cube_compute_store/data_copy_l0_c_to_l1.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。F322F16/F322BF16 为 Cast 模式，DEQF16/VDEQF16/REQ8/VREQ8 等为 scalar/tensor 量化，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”要求 L0C→L1 的 tensor 量化先设置 FixPipe 寄存器；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。”定义 SetFixPipeConfig 覆盖该通路的 tensor 参数。该边直接用于校验量化搬出的前置调用。
<!-- cannbot:related:end -->
