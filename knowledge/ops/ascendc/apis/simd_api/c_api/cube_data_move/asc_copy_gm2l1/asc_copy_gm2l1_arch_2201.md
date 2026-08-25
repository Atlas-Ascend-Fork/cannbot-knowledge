---
type: API
title: asc_copy_gm2l1
description: 将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_gm2l1

将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数的起始地址。；size(输入): 搬运数据大小（字节）。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为DataBlock（32字节）。取值范围：[1, 65535]。；src_gap(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst(输出): 目的操作数（矢量）的起始地址。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_gm2l1指令，且asc_copy_gm2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_copy_gm2l1_nd2nz](../asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_2201.md)（`related`）：“asc_copy_gm2l1_nd2nz”定义：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；“asc_copy_gm2l1”定义：将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。。实质衔接：架构变体共享 GM→L1 与 ND→NZ 任务但支持的转换和 padding 不同；基础 GM→L1 与 DN→NZ 用于选择是否需要格式转换。
- [asc_copy_l12l0a](../asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`related`）：asc_copy_l12l0a 与《asc_copy_gm2l1》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyGm2L1](asc_copy_gm2l1.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1正文界定“将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1正文说明“将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_3510.md)（`same_topic`）：asc_copy_gm2l1说明将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式；对asc_copy_gm2l1而言，GM→L1 搬运需按普通、ND2NZ、Align 重载选择；arch3510 的 loop1 stride SPR 必须在对应搬运前配置。
<!-- cannbot:related:end -->
