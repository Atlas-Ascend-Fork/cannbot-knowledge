---
type: API
title: asc_copy_gm2l1_nd2nz
description: 将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_gm2l1_nd2nz

将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数的起始地址。；nd_num(输入): 传输ND矩阵的数目，取值范围：nd_num∈[0, 4095]。；n_value(输入): ND矩阵的行数，取值范围：n_value∈[0, 16384]。；d_value(输入): ND矩阵的列数，取值范围：d_value∈[0, 65535]。；src_nd_matrix_stride(输入): 源操作数相邻ND矩阵起始地址间的偏移，取值范围：src_nd_matrix_stride∈[0, 65535]，单位为元素。；src_d_value(输入): 源操作数同一ND矩阵的相邻行起始地址间的偏移，取值范围：src_d_value∈[1, 65535]，单位为元素。；dst_nz_c0_stride(输入): ND转换到NZ格式后，源操作数中的一行会转换为目的操作数的多行。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_gm2l1_nd2nz指令，且asc_copy_gm2l1_nd2nz指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1_nd2nz指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l1Dn2nz](../asc_copy_gm2l1_dn2nz.md)（`related`）：“asc_copy_gm2l1_nd2nz”定义：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；“AscCopyGm2l1Dn2nz”定义：将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。。实质衔接：架构变体共享 GM→L1 与 ND→NZ 任务但支持的转换和 padding 不同；基础 GM→L1 与 DN→NZ 用于选择是否需要格式转换。
- [asc_copy_gm2l1](../asc_copy_gm2l1/asc_copy_gm2l1_arch_2201.md)（`related`）：“asc_copy_gm2l1_nd2nz”定义：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；“asc_copy_gm2l1”定义：将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。。实质衔接：架构变体共享 GM→L1 与 ND→NZ 任务但支持的转换和 padding 不同；基础 GM→L1 与 DN→NZ 用于选择是否需要格式转换。
- [AscCopyGm2L1](../asc_copy_gm2l1/asc_copy_gm2l1.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1_nd2nz正文界定“将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [AscCopyGm2L1Nd2Nz](asc_copy_gm2l1_nd2nz.md)（`same_topic`）：AscCopyGm2L1Nd2Nz 是 ND→NZ 的 GM→L1 接口组，asc_copy_gm2l1_nd2nz_arch_2201 是该组在 2201 架构上的具体入口；两卡共享同一搬运与格式转换合同。
- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1_nd2nz正文说明“将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz_arch_3510.md)（`same_topic`）：“asc_copy_gm2l1_nd2nz”定义：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；“asc_copy_gm2l1_nd2nz”定义：将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以ND类型存储；L1中的数据以NZ形式存储。 ND->NZ的搬运形式如下图： !。实质衔接：架构变体共享 GM→L1 与 ND→NZ 任务但支持的转换和 padding 不同；基础 GM→L1 与 DN→NZ 用于选择是否需要格式转换。
<!-- cannbot:related:end -->
