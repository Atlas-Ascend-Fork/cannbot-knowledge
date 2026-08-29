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

- [AscCopyL0c2Gm](asc_copy_l0c2gm_arch_3510.md)（`same_topic`）：该接口用于将矩阵计算的结果从L0C Buffer搬运至Global Memory（GM）中，并且在搬运过程中支持与其它接口组合使用，配置多种随路能力；矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到GM中。两卡的核心对象都是 AscCopyL0c2Gm 的 L0C 到 GM 搬运与随路量化，分别给出 3510 组合能力和 2201 九种量化模式。
<!-- cannbot:related:end -->
