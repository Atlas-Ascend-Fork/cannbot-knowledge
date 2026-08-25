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

- [AscCopyL0c2L1](../asc_copy_l0c2l1/asc_copy_l0c2l1_arch_3510.md)（`related`）：两接口共享 L0C 搬出与随路处理，但目的存储分别为 GM 与 L1，构成下一阶段消费位置驱动的直接选型。
- [AscCopyL12gm](../asc_copy_l12gm.md)（`related`）：AscCopyL12gm 与《AscCopyL0c2Gm》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
- [AscSetL0c2gmChannelPara](../../sys_var/asc_set_l0c2gm_channel_para.md)（`related`）：AscCopyL0c2Gm说明将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力；对AscSetL0c2gmChannelPara而言，ChannelPara 只在 NZ2DN 的 L0C 搬运前生效；Channel Split 的格式限制和 AscCopyL0c2Gm 的参数共同界定有效调用。
- [AscCopyL0c2Gm](asc_copy_l0c2gm.md)（`same_topic`）：AscCopyL0c2Gm说明将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力。
- [AscCopyL0c2Gm](asc_copy_l0c2gm_arch_2201.md)（`same_topic`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscCopyL0c2Gm》补充：将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力。
<!-- cannbot:related:end -->
