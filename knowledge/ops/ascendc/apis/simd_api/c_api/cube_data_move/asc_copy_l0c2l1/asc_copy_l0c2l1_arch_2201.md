---
type: API
title: AscCopyL0c2L1
description: 矩阵计算完成后对结果进行量化处理，并将处理结果搬运到L1 Buffer中，支持9种量化模式。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l0c2l1/asc_copy_l0c2l1_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# AscCopyL0c2L1

矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到L1 Buffer中。量化模式共分为9种，分别为
- NoQuant：不开启量化功能。
- DEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。
- F322BF16：float量化成bfloat16_t。量化结果不支持INF_NAN模式。
- F322F16：float量化成half。量化结果不支持INF_NAN模式。
- QF322B8_PRE：float量化成uint8_t/int8_t。scalar量化。
- REQ8：int32_t量化成uint8_t/int8_t。scalar量化。
- VDEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。
- VQF322B8_PRE：float量化成uint8_t/int8_t。矢量量化。
- VREQ8：int32_t量化成uint8_t/int8_t。矢量量化。

此外，该搬运指令还支持int4b_t类型的量化，相关量化类型分为两种：int32_t量化为int4b_t；float量化为int4b_t。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数的起始地址。；n_size(输入): 源NZ矩阵在N方向上的大小。 • 不开启NZ2ND功能，取值范围：[1, 4095]； • 开启NZ2ND功能，取值范围：[1, 4095]。；m_size(输入): 源NZ矩阵在M方向上的大小。 • 不开启NZ2ND功能，取值范围：[1, 65535]； • 开启NZ2ND功能，取值范围：[1, 8192]。；dst_stride(输入): • 不开启NZ2ND功能，目的NZ矩阵中相邻Z排布的起始地址偏移，取值不为0，单位：element。 • 开启NZ2ND/NZ2DN功能，目的ND矩阵每一行中的元素个数，取值不为0 ，单位：element。；src_stride(输入): 源NZ矩阵中相邻Z排布的起始地址偏移，取值范围：[0, 65535]，单位：C0_Size(16*sizeof(T), T为src的数据类型)。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_l0c2l1指令，且asc_copy_l0c2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_l0c2l1指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetL0cCopyParams](../asc_set_l0c_copy_params.md)（`related`）：AscCopyL0c2L1：AscCopyL0c2L1的2201/3510卡核对同一搬运原型，DataCopyL0CToL1提供C++对应语义，AscSetL0cCopyParams配置该L0C搬出的通用参数。 目标卡《AscSetL0cCopyParams》补充：设置L0C搬运随路格式转换（NZ转ND）的相关配置。
- [AscCopyL0c2L1](asc_copy_l0c2l1.md)（`same_topic`）：AscCopyL0c2L1：AscCopyL0c2L1的2201/3510卡核对同一搬运原型，DataCopyL0CToL1提供C++对应语义，AscSetL0cCopyParams配置该L0C搬出的通用参数。 目标卡《AscCopyL0c2L1》补充：将数据从L0C搬运到L1 Buffer的接口，包含不同架构版本的具体实现。
- [AscCopyL0c2L1](asc_copy_l0c2l1_arch_3510.md)（`same_topic`）：AscCopyL0c2L1：AscCopyL0c2L1的2201/3510卡核对同一搬运原型，DataCopyL0CToL1提供C++对应语义，AscSetL0cCopyParams配置该L0C搬出的通用参数。 目标卡《AscCopyL0c2L1》补充：将矩阵计算结果从L0C Buffer搬运至L1 Buffer，搬运过程中支持随路量化、ReLU、格式转换等能力。
- [AscSetL0c2gmQuantPost](../../sys_var/asc_set_l0c2gm_quant_post.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscCopyL0c2L1正文说明“矩阵计算完成后对结果进行量化处理，并将处理结果搬运到L1 Buffer中，支持9种量化模式”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [DataCopyL0CToL1](../../../basic_api/cube_compute/cube_compute_store/data_copy_l0_c_to_l1.md)（`same_topic`）：AscCopyL0c2L1：AscCopyL0c2L1的2201/3510卡核对同一搬运原型，DataCopyL0CToL1提供C++对应语义，AscSetL0cCopyParams配置该L0C搬出的通用参数。 目标卡《DataCopyL0CToL1》补充：将L0C Buffer中的矩阵计算结果搬运至L1 Buffer，支持随路量化和ReLU激活。
<!-- cannbot:related:end -->
