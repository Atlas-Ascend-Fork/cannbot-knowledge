---
type: API
title: AscCopyL12l0bMx
description: 将Mx scale矩阵从L1 Buffer搬运到L0B Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b_mx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCopyL12l0bMx

将Mx scale矩阵从L1 Buffer搬运到L0B Buffer。

参数：dst(输出): 目的操作数的地址。；src(输入): 源操作数（Mx scale矩阵）的起始地址，数据类型为fp8_e8m0_t。；x_start_pos(输入): 源操作数X轴方向的起始位置，即M维度方向，单位为1个分形（1个单位代表一个32B的分形）。；y_start_pos(输入): 源操作数Y轴方向的起始位置，即K维度方向，单位为32B。；x_step(输入): 源操作数X轴方向搬运长度，即M维度方向，单位为1个分形（1个单位代表一个32B的分形）。取值范围：[0, 255]。；y_step(输入): 源操作数Y轴方向搬运长度，即K维度方向，单位为32B。取值范围：[0, 255]。；src_stride(输入): 源操作数X轴方向前一个分形起始地址与后一个分形起始地址的间隔，单位为32B。；dst_stride(输入): 目的操作数X轴方向前一个分形起始地址与后一个分形起始地址。

约束：- 各存储单元的空间大小和对齐要求
- scale矩阵的分形固定为(16, 2, 16)，对应L0B Buffer的分形为(16, 32, 16)，占L0B Buffer地址的1 / 16，需要按照这种地址约束存放地址。
- dst（L0B Buffer的地址）的数据类型支持fp4x2_e2m1_t、fp4x2_e1m2_t、fp8_e5m2_t、fp8_e4m3fn_t，src的数据类型支持fp8_e8m0_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMmadMx](../cube_compute/asc_mmad_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《AscCopyL12l0bMx》说明将Mx scale矩阵从L1 Buffer搬运到L0B Buffer。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [asc_copy_l12l0b](asc_copy_l12l0b/asc_copy_l12l0b_arch_3510.md)（`related`）：MX 量化 B 路径需要专用格式/scale 搬运。
- [AscCopyGm2l0b](asc_copy_gm2l0b.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscCopyGm2l1Align](asc_copy_gm2l1_align.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l1Align》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscCopyGm2l1Dn2nz](asc_copy_gm2l1_dn2nz.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l1Dn2nz》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscCopyL12L0b](asc_copy_l12l0b/asc_copy_l12l0b.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyL12L0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscCopyL12l0aMx](asc_copy_l12l0a_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyL12l0aMx》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscCopyL12l0bSparse](asc_copy_l12l0b_sparse.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyL12l0bSparse》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetGm2l1Loop1Stride](asc_set_gm2l1_loop1_stride.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetGm2l1Loop1Stride》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetGm2l1Loop2Stride](asc_set_gm2l1_loop2_stride.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetGm2l1Loop2Stride》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetGm2l1LoopSize](asc_set_gm2l1_loop_size.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetGm2l1LoopSize》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetGm2l1Pad](asc_set_gm2l1_pad.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetGm2l1Pad》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetL13dFmatrix](asc_set_l13d_fmatrix.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetL13dFmatrix》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetL13dFmatrixB](asc_set_l13d_fmatrix_b.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetL13dFmatrixB》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetL13dSize](asc_set_l13d_size.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetL13dSize》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_gm2l1](asc_copy_gm2l1/asc_copy_gm2l1_arch_3510.md)（`same_topic`）：AscCopyL12l0bMx 与《asc_copy_gm2l1》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_l12l0b](asc_copy_l12l0b/asc_copy_l12l0b_arch_2201.md)（`same_topic`）：AscCopyL12l0bMx 与《asc_copy_l12l0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [矩阵数据搬运](cube_data_move.md)（`same_topic`）：AscCopyL12l0bMx 与《矩阵数据搬运》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
<!-- cannbot:related:end -->
