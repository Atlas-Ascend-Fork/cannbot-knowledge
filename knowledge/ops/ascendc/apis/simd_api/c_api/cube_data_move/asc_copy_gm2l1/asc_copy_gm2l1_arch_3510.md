---
type: API
title: asc_copy_gm2l1
description: 将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。
  - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# asc_copy_gm2l1

将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式
- 填充模式：搬运过程中可以对数据进行填充或移除填充值。
- 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为32个字节。；pad_func_mode(输入): 一个4Bit的值，用于指示通道上的padding功能，他会在32个字节的数据中填充数据；或从每个32个字节的读取数据中移除padding值。 • 0：不做padding。 • 1：每有1个字节的数据，插入31个padding值。 • 2：每有2个字节的数据，插入15个padding值。 • 3：每有4个字节的数据，插入14个padding值。 • 4：每有8个字节的数据，插入12个padding值。 • 5：每有16个字节的数据，插入8个padding值。 • 6：每有32个字节的数据，移除28个最高有效位数据，只保留4个最低有效位元素。 • 7：每有32个字节的数据，移除24个最高有效位数据，只保留8个最低有效位元素。 • 8：每有32个字节的数据，移除16个最高有效位数据，只保留16个最低有效位元素。；src_stride(输入): 输入数据中两个相邻连续数据块之间的距离。；dst_stride(输入): 输出数据中两个相邻连续数据块之间的距离。；dst(输出): 目的操作数（矢量）的起始地址。

约束：各存储单元的空间大小和对齐要求

### 填充模式约束

- 对于插入padding值的场景
    - len_burst的单位为32个字节的指的是写入L1 Buffer的实际数据数，它必须设置为1，此时一次仅从GM里读取1/2/4/8/16个字节的数据。
    - 每一次burst都是从GM中连续读取，因此不需要设置src_stride。
    - dst_stride以32个字节为单位。
- 对于移除padding值的场景
    - 源操作数中一次burst操作的数据为len_burst * 32个字节，目的操作数中一次burst的实际数据为len_burst * 4/8/16个字节。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetGm2l1Loop1Stride](../asc_set_gm2l1_loop1_stride.md)（`related`）：AscSetGm2l1Loop1Stride说明设置GM到L1搬运时内层循环中相邻迭代数据块间的间隔；对asc_copy_gm2l1而言，GM→L1 搬运需按普通、ND2NZ、Align 重载选择；arch3510 的 loop1 stride SPR 必须在对应搬运前配置。
- [asc_copy_gm2l1_nd2nz](../asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz_arch_3510.md)（`related`）：asc_copy_gm2l1_nd2nz说明将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以ND类型存储；L1中的数据以NZ形式存储。 ND->NZ的搬运形式如下图： !；对asc_copy_gm2l1而言，GM→L1 搬运需按普通、ND2NZ、Align 重载选择；arch3510 的 loop1 stride SPR 必须在对应搬运前配置。
- [asc_copy_l12l0a](../asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`related`）：asc_copy_l12l0a 与《asc_copy_gm2l1》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyGm2L1](asc_copy_gm2l1.md)（`same_topic`）：焦点处理GM→L1 搬运的基础、对齐与 ND2NZ 变体；asc_copy_gm2l1正文界定“将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。 - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持”。候选只覆盖 GM→L1 原始、对齐与 ND/DN→NZ 搬运变体，便于按布局选择接口。
- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；asc_copy_gm2l1正文说明“将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。 - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyL12l0bMx](../asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《asc_copy_gm2l1》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_2201.md)（`same_topic`）：asc_copy_gm2l1说明将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式；对asc_copy_gm2l1而言，GM→L1 搬运需按普通、ND2NZ、Align 重载选择；arch3510 的 loop1 stride SPR 必须在对应搬运前配置。
<!-- cannbot:related:end -->
