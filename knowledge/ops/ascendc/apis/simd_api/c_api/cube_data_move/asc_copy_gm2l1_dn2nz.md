---
type: API
title: AscCopyGm2l1Dn2nz
description: 将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_dn2nz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCopyGm2l1Dn2nz

将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行DN->NZ/NCHW->NC1HWC0/NCHW->C1HWNC0操作。若D未对齐C0的大小，将会在L1 Buffer的最内层维度填充0值。GM中的数据以DN类型存储；L1中的数据以NZ形式存储。

DN->NZ的搬运形式如下图

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；loop1_src_stride(输入): 搬运过程中最内层循环相邻迭代源操作数的数据块间的间隔，单位为字节。；l2_cache_ctl(输入): 配置数据在L2 Cache中的管理策略。取值说明请参见表2。；n_value(输入): 源操作数中DN排布中的N值。；d_value(输入): 源操作数中DN排布中的D值。；loop4_src_stride(输入): 搬运过程中最外层循环相邻迭代源操作数的数据块间的间隔，单位为字节。；smallc0_en(输入): SmallC0模式开关：   &bull; true：C0_SIZE会被pad至32个字节。  &bull; false：C0_SIZE会被pad为4个c。

约束：- 各存储单元的空间大小和对齐要求
- 注意当且仅当D <= 4时，smallc0_en才可以被启用，否则它会失效。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1Nd2Nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md)（`related`）：AscCopyGm2l1Dn2nz说明将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。
- [AscSetGm2l1NzPara](../sys_var/asc_set_gm2l1_nz_para.md)（`related`）：AscSetGm2l1NzPara 明确在 asc_copy_gm2l1_dn2nz 前配置 MTE2_NZ_PARA，是寄存器设置的直接消费者。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_2201.md)（`related`）：“asc_copy_gm2l1_nd2nz”定义：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；“AscCopyGm2l1Dn2nz”定义：将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。。实质衔接：架构变体共享 GM→L1 与 ND→NZ 任务但支持的转换和 padding 不同；基础 GM→L1 与 DN→NZ 用于选择是否需要格式转换。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_3510.md)（`related`）：ND2NZ 与 DN2NZ 都完成 GM→L1 的 NZ 转换，但源布局和 stride/循环契约不同，适合直接选型对照。
- [AscCopyGm2L1](asc_copy_gm2l1/asc_copy_gm2l1.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；AscCopyGm2l1Dn2nz正文界定“将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [AscCopyGm2l1Align](asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2l1Dn2nz正文说明“将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l1Dn2nz》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [DataCopy](../../basic_api/cube_compute/cube_compute_load/data_copy_gm_to_l1_dn2_nz.md)（`same_topic`）：两张卡都描述 GM 到 L1 的 DN2NZ 搬运与同一格式转换方向，一张是 C++ Basic API，另一张是 C API 对应入口。
<!-- cannbot:related:end -->
