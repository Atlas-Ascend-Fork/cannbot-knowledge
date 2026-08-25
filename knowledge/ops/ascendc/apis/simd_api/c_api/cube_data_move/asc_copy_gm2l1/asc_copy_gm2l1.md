---
type: API
title: AscCopyGm2L1
description: GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscCopyGm2L1

GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。

将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。

本接口组包含 asc_copy_gm2l1_arch_2201, asc_copy_gm2l1_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2l1指令，且asc_copy_gm2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1指令的串行化，防止出现异常数据。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1Nd2Nz](../asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md)（`related`）：AscCopyGm2L1说明GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。
- [AscCopyGm2l0b](../asc_copy_gm2l0b.md)（`related`）：AscCopyGm2L1 提供先从 GM 搬到 L1 的通用阶段，可与 L1→L0B 组合替代不支持的 GM→L0B 直达通路。
- [AscSetGm2l1LoopSize](../asc_set_gm2l1_loop_size.md)（`related`）：AscCopyGm2L1 consumes the loop-size state configured by AscSetGm2l1LoopSize when performing GM-to-L1 transfer.
- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscCopyGm2L1正文说明“GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyGm2l1Dn2nz](../asc_copy_gm2l1_dn2nz.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；AscCopyGm2l1Dn2nz正文界定“将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_2201.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1正文界定“将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_3510.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1正文界定“将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。 - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [asc_copy_gm2l1_nd2nz](../asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_2201.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1_nd2nz正文界定“将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [asc_copy_gm2l1_nd2nz](../asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_3510.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1_nd2nz正文界定“将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
<!-- cannbot:related:end -->
