---
type: API
title: AscCopyL0c2Gm
description: 将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscCopyL0c2Gm

该接口用于将矩阵计算的结果从L0C Buffer搬运至Global Memory（GM）中，并且在搬运过程中支持与其它接口组合使用，配置多种随路能力。

下图

quant_pre_mode量化模式参数支持的枚举值
- NoQuant：不开启量化功能
- DEQF16：int32_t量化成half， scalar量化
- VDEQF16：int32_t量化成half，tensor量化
- REQ4：int32_t量化成int4b_t，scalar量化
- VREQ4：int32_t量化成int4b_t，tensor量化
- REQ8：int32_t量化成int8_t/uint8_t，scalar量化
- VREQ8：int32_t量化成int8_t/uint8_t，tensor量化
- QS322BF16_PRE：int32_t量化成bfloat16_t，scalar量化
- VQS322BF16_PRE：int32_t量化成bfloat16_t，tensor量化

参数：dst(输出): 目的操作数的起始地址。数据格式为NZ、ND或DN格式。ND格式的地址需要满足1字节对齐，NZ和DN格式的地址需要满足32字节对齐。；src(输入): 源操作数的起始地址。数据格式为NZ格式，地址需要满足64字节对齐。；n_size(输入): 源NZ矩阵在N方向上的大小，取值范围：[1, 4095]。；m_size(输入): 源NZ矩阵在M方向上的大小。 • 不开启NZ2ND功能，取值范围：[1, 65535]； • 开启NZ2ND功能，取值范围：[1, 8192]。；dst_stride(输入): • 若不开启NZ2ND功能，dst_stride表示目的NZ矩阵中相邻Z排布的起始地址偏移，取值不为0，单位：element。 • 若开启NZ2ND/NZ2DN功能，dst_stride表示目的ND矩阵每一行中的元素个数，取值不为0，单位：element。；src_stride(输入): 源NZ矩阵中相邻Z排布的起始地址偏移，取值范围：[0, 65535]，单位：C0_Size(16*sizeof(T)，T为src的数据类型)。

约束：- 各存储单元的空间大小和对齐要求

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetL0c2gmChannelPara](../../sys_var/asc_set_l0c2gm_channel_para.md)（`related`）：“对通道步长参数的专用寄存器的比特位进行设置。需要配合接口asc_copy_l0c2l1或asc_copy_l0c2gm使用。 仅当调用接口时开启NZ2DN模式时，此功能才有效。”与“该接口用于将矩阵计算的结果从L0C Buffer搬运至Global Memory（GM）中，并且在搬运过程中支持与其它接口组合使用，配置多种随路能力。”提供双方正文证据。setter 正文直接指定 asc_copy_l0c2gm 且只在 NZ2DN 模式生效，搬运卡定义 L0C 到 GM 及组合随路能力，形成配置先于搬运的调用关系。
- [AscCopyL0c2Gm](asc_copy_l0c2gm_arch_2201.md)（`same_topic`）：该接口用于将矩阵计算的结果从L0C Buffer搬运至Global Memory（GM）中，并且在搬运过程中支持与其它接口组合使用，配置多种随路能力；矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到GM中。两卡的核心对象都是 AscCopyL0c2Gm 的 L0C 到 GM 搬运与随路量化，分别给出 3510 组合能力和 2201 九种量化模式。
<!-- cannbot:related:end -->
