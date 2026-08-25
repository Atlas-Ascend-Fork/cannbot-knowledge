---
type: API
title: AscCopyGm2l1Align
description: 对矩阵数据进行实时padding后从GM搬运到L1 Buffer，需配合asc_set_gm2l1系列接口使用。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_align.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscCopyGm2l1Align

对矩阵数据进行实时padding，完成padding后将数据从Global Memory搬运到L1 Buffer。需要与asc_set_gm2l1_loop_size、asc_set_gm2l1_loop1_stride、asc_set_gm2l1_loop2_stride和asc_set_gm2l1_pad配合使用。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为字节。；left_padding_count(输入): 数据左侧的padding元素数。对位宽为8的数据类型，该参数的最大值为32，对位宽为16的数据类型，该参数的最大值为16，对位宽为32的数据类型，该参数的最大值为8。；right_padding_count(输入): 数据右侧的padding元素数。对位宽为8的数据类型，该参数的最大值为32，对位宽为16的数据类型，该参数的最大值为16，对位宽为32的数据类型，该参数的最大值为8。；data_select_bit(输入): padding数据选择位，当前只支持设置为false，将padding值设置为数据块的第一个元素。

约束：- 各存储单元的空间大小和对齐要求
- 目的操作数不得存在地址重叠。对于存在地址重叠的操作，硬件将不返回任何警告或错误，也无法保证地址重叠数据的正确性。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1](asc_copy_gm2l1/asc_copy_gm2l1.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2L1正文说明“GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyGm2L1Nd2Nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2L1Nd2Nz正文说明“GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyGm2l1Dn2nz](asc_copy_gm2l1_dn2nz.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2l1Dn2nz正文说明“将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l1Align》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetGm2l1Loop1Stride](asc_set_gm2l1_loop1_stride.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscSetGm2l1Loop1Stride正文说明“设置GM到L1搬运时内层循环中相邻迭代数据块间的间隔”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscSetGm2l1Loop2Stride](asc_set_gm2l1_loop2_stride.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscSetGm2l1Loop2Stride正文说明“设置GM到L1搬运时外层循环中相邻迭代数据块间的间隔”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscSetGm2l1LoopSize](asc_set_gm2l1_loop_size.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscSetGm2l1LoopSize正文说明“设置GM到L1搬运流程中的循环次数”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscSetGm2l1Pad](asc_set_gm2l1_pad.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscSetGm2l1Pad正文说明“设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1](asc_copy_gm2l1/asc_copy_gm2l1_arch_2201.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1正文说明“将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1](asc_copy_gm2l1/asc_copy_gm2l1_arch_3510.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1正文说明“将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。 - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_2201.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1_nd2nz正文说明“将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_3510.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1_nd2nz正文说明“将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以ND类型存储；L1中的数据以NZ形式存储”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
<!-- cannbot:related:end -->
