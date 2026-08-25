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

<!-- cannbot:related:start -->
## 相关

- [FixpipeL0CToGM](fixpipe_l0_c_to_gm.md)（`related`）：FixpipeL0CToGM 与本卡共享量化、ReLU、格式转换机制，但目的存储从 L1 改为 GM，可用于按后续消费者位置选择搬出通路。
- [FixpipeL0CToUB](fixpipe_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 提供 L0C 结果直接交给 Vector 侧 UB 的通路，与 L0CToL1 的缓存复用场景形成明确的目的空间选型。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《FixpipeL0CToL1》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToL1》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [DataCopyL0CToL1](data_copy_l0_c_to_l1.md)（`same_topic`）：FixpipeL0CToL1 与该 DataCopy 都完成 L0C→L1，并覆盖量化/激活等搬出处理；两张卡给出同一搬出对象的接口形态与约束切面。
<!-- cannbot:related:end -->
