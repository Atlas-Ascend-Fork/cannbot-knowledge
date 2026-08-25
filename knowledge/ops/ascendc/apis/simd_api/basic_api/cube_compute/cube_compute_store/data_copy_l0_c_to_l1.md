---
type: API
title: DataCopyL0CToL1
description: 将L0C Buffer中的矩阵计算结果搬运至L1 Buffer，支持随路量化和ReLU激活。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopyL0CToL1

将 L0C Buffer（CO1）中 Mmad 计算结果搬运至 L1 Buffer，支持随路量化和 ReLU 激活，不支持 NoQuant 模式。头文件 `basic_api/kernel_operator_data_copy_intf.h`。

参数：dst 为 LocalTensor（L1，NZ 格式 32 字节对齐）；src 为 LocalTensor（L0C，NZ 格式 64 字节对齐）；intriParams 为 DataCopyCO12DstParams。关键字段：nSize[0,4095]须为 16 倍数，mSize[0,65535]，dstStride、srcStride、unitFlag(0/2/3)、quantPre(QuantMode_t)、reluPre(0/1)。此通路不支持 NZ2ND 和 channelSplit。

数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。F322F16/F322BF16 为 Cast 模式，DEQF16/VDEQF16/REQ8/VREQ8 等为 scalar/tensor 量化，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。

约束：mSize 或 nSize 为 0 时为 NOP；量化参数不能为 inf/nan/非规格化数。支持 950/a2/a3，不支持 Atlas 推理/训练系列。
