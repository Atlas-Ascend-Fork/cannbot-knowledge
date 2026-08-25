---
type: API
title: AscCopyGm2L1Nd2Nz
description: GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscCopyGm2L1Nd2Nz

GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本。

将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。

本接口组包含 asc_copy_gm2l1_nd2nz_arch_2201, asc_copy_gm2l1_nd2nz_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2l1_nd2nz指令，且asc_copy_gm2l1_nd2nz指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1_nd2nz指令的串行化，防止出现异常数据。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1](../asc_copy_gm2l1/asc_copy_gm2l1.md)（`related`）：AscCopyGm2L1说明GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。
- [AscCopyGm2l1Dn2nz](../asc_copy_gm2l1_dn2nz.md)（`related`）：AscCopyGm2l1Dn2nz说明将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。
- [AscSetGm2l1Loop1Stride](../asc_set_gm2l1_loop1_stride.md)（`related`）：AscSetGm2l1Loop1Stride说明设置GM到L1搬运时内层循环中相邻迭代数据块间的间隔。
- [AscSetGm2l1Loop2Stride](../asc_set_gm2l1_loop2_stride.md)（`related`）：AscSetGm2l1Loop2Stride说明设置GM到L1搬运时外层循环中相邻迭代数据块间的间隔。
- [AscSetGm2l1LoopSize](../asc_set_gm2l1_loop_size.md)（`related`）：AscSetGm2l1LoopSize说明设置GM到L1搬运流程中的循环次数。
- [AscSetGm2l1Pad](../asc_set_gm2l1_pad.md)（`related`）：AscSetGm2l1Pad说明设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值。
- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2L1Nd2Nz正文说明“GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz_arch_2201.md)（`same_topic`）：AscCopyGm2L1Nd2Nz 是 ND→NZ 的 GM→L1 接口组，asc_copy_gm2l1_nd2nz_arch_2201 是该组在 2201 架构上的具体入口；两卡共享同一搬运与格式转换合同。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz_arch_3510.md)（`same_topic`）：asc_copy_gm2l1_nd2nz说明将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以ND类型存储；L1中的数据以NZ形式存储。 ND->NZ的搬运形式如下图： !。
<!-- cannbot:related:end -->
