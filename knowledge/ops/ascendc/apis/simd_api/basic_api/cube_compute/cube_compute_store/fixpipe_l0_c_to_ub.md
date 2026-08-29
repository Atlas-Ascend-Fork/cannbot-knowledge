---
type: API
title: FixpipeL0CToUB
description: 将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# FixpipeL0CToUB

Fixpipe 是 L0C Buffer→Unified Buffer 的组合搬出接口，内部封装寄存器设置与数据搬运。头文件 `basic_api/kernel_operator_fixpipe_intf.h`。支持随路 scalar/tensor 量化、ReLU 和 NZ2ND/NZ2NZ/NZ2DN 格式转换。

按平台使用参数结构体：FixpipeParamsArch3510（950，支持 FP8/HIF8 等扩展量化模式）、FixpipeParamsM300（Atlas 200I/500 A2）。调用时模板 config 不能直接用 CFG_ROW_MAJOR 等预设值，须显式构造 `isToUB = true` 的 FixpipeConfig。

参数：dst 为 LocalTensor（UB，32B 对齐）；src 为 LocalTensor（L0C，NZ 64B 对齐）；intriParams；cbufWorkspace（tensor 量化参数，L1 32B 对齐）。关键字段：nSize[0,4095]、mSize[0,65535]、srcStride、dstStride、quantPre、deqScalar、reluEn、unitFlag(0/2/3)、dualDstCtrl（950 双目标模式 2'b00/01/10，按 M 或 N 维度拆分到两个 Vector Core 的 UB）、subBlockId。

数据类型 950：float→{int8_t,uint8_t,hifloat8_t,fp8_e4m3fn_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,bfloat16_t,int32_t}。Atlas 200I/500 A2：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。约束：mSize/nSize/ndNum 为 0 时 NOP；目标数据不能重叠写入；dualDstCtrl 仅支持 NZ2NZ/NZ2ND 场景。支持 950 和 Atlas 200I/500 A2。
