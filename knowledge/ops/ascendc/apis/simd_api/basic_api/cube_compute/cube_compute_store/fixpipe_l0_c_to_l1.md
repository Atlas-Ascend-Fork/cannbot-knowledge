---
type: API
title: FixpipeL0CToL1
description: 将L0C Buffer中的矩阵计算结果搬运至L1 Buffer，支持随路量化和ReLU激活的组合接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# FixpipeL0CToL1

Fixpipe 是 L0C Buffer→L1 Buffer 的组合搬出接口，内部封装寄存器设置与数据搬运。头文件 `basic_api/kernel_operator_fixpipe_intf.h`、`basic_api/kernel_operator_data_copy_intf.h`。

支持随路 scalar/tensor 量化和 ReLU，不支持 NoQuant 模式。按平台使用不同参数结构体：FixpipeParamsArch3510（950，支持 FP8/HIF8 等扩展量化模式）、FixpipeParamsV220（a2/a3）。不支持 FixpipeParamsM300。模板 config 取 CFG_ROW_MAJOR(NZ2ND)、CFG_NZ(NZ2NZ)、CFG_COLUMN_MAJOR(NZ2DN，仅 950)。

参数：dst 为 LocalTensor（L1，NZ 32B 对齐）；src 为 LocalTensor（L0C，NZ 64B 对齐）；intriParams 为对应平台参数；cbufWorkspace 为 tensor 量化参数（L1，32B 对齐）。关键字段：nSize[0,4095]须 16 倍数、mSize[0,65535]、srcStride、dstStride、quantPre、deqScalar、reluEn、unitFlag(0/2/3)、ndNum/srcNdStride/dstNdStride。

数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。约束：mSize/nSize/ndNum 为 0 时 NOP；量化参数不能为 inf/nan/非规格化数。支持 950/a2/a3/Kirin X90/9030，不支持 Atlas 200I/500 A2。
