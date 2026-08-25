---
type: API
title: AscCopyL0c2Gm
description: 矩阵计算完成后对结果进行量化处理，并将处理结果搬运到GM中，支持9种量化模式。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# AscCopyL0c2Gm

矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到GM中。量化模式共分为9种，分别为
- NoQuant：不开启量化功能。
- F322F16：float量化成half。量化结果不支持INF_NAN模式。
- F322BF16：float量化成bfloat16_t。量化结果不支持INF_NAN模式。
- DEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。
- VDEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。
- QF322B8_PRE：float量化成uint8_t/int8_t。scalar量化。
- VQF322B8_PRE：float量化成uint8_t/int8_t。矢量量化。
- REQ8：int32_t量化成uint8_t/int8_t。scalar量化。
- VREQ8：int32_t量化成uint8_t/int8_t。矢量量化。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；n_size(输入): 源NZ矩阵在N方向上的大小。 - 不开启NZ2ND功能：若开启channel_split功能，n_size必须为8的倍数，取值范围为[1, 4095]。若不开启channel_split功能，n_size必须为16的倍数，取值范围为[1, 4095]。 - 开启NZ2ND功能：m_size的取值范围为[1, 4095]。；m_size(输入): 源NZ矩阵在M方向上的大小。 - 不开启NZ2ND功能：取值范围为[1, 65535]。 - 开启NZ2ND功能，m_size的取值范围为[1, 8192]。；dst_stride_dst_d(输入): - 不开启NZ2ND功能,目的NZ矩阵中相邻Z排布的起始地址偏移，取值不为0，单位：element。 - 开启NZ2ND/NZ2DN功能,目的ND矩阵每一行中的元素个数，取值不为0 ，单位：element。；src_stride(输入): 源NZ矩阵中相邻Z排布的起始地址偏移，取值范围：[0, 65535]，单位：C0_Size(16*sizeof(T), T为src的数据类型)。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12gm](../asc_copy_l12gm.md)（`related`）：AscCopyL12gm 与《AscCopyL0c2Gm》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
- [AscSetL0c2gmChannelPara](../../sys_var/asc_set_l0c2gm_channel_para.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0c2gmChannelPara》补充：设置通道步长寄存器比特位，配合L0C搬运接口使用。
- [AscSetL0c2gmLreluAlpha](../asc_set_l0c2gm_lrelu_alpha.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0c2gmLreluAlpha》补充：设置L0C搬运接口计算过程中使用的Leaky ReLU alpha值。
- [AscSetL0cCopyParams](../asc_set_l0c_copy_params.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0cCopyParams》补充：设置L0C搬运随路格式转换（NZ转ND）的相关配置。
- [AscSetL0cCopyPrequant](../asc_set_l0c_copy_prequant.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0cCopyPrequant》补充：设置数据搬运随路量化流程中的标量量化参数。
- [FixpipeL0CToGM](../../../basic_api/cube_compute/cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《FixpipeL0CToGM》补充：将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。
- [NZ2ND](../../../basic_api/cube_compute/cube_store_key_features/nz2_nd.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《NZ2ND》补充：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。
- [AscCopyL0c2Gm](asc_copy_l0c2gm.md)（`same_topic`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscCopyL0c2Gm》补充：将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。
- [AscCopyL0c2Gm](asc_copy_l0c2gm_arch_3510.md)（`same_topic`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscCopyL0c2Gm》补充：将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力。
<!-- cannbot:related:end -->
