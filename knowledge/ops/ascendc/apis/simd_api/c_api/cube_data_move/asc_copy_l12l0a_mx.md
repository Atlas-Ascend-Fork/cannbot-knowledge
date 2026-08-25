---
type: API
title: AscCopyL12l0aMx
description: 将Mx scale矩阵从L1 Buffer搬运到L0A Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0a_mx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCopyL12l0aMx

将Mx scale矩阵从L1 Buffer搬运到L0A Buffer。

参数：dst(输出): 目的操作数的地址。；src(输入): 源操作数（Mx scale矩阵）的起始地址，数据类型为fp8_e8m0_t。；x_start_pos(输入): 源操作数X轴方向的起始位置，即M维度方向，单位为1个分形（1个单位代表一个32B的分形）。；y_start_pos(输入): 源操作数Y轴方向的起始位置，即K维度方向，单位为32B。；x_step(输入): 源操作数X轴方向搬运长度，即M维度方向，单位为1个分形（1个单位代表一个32B的分形）。取值范围：[0, 255]。；y_step(输入): 源操作数Y轴方向搬运长度，即K维度方向，单位为32B。取值范围：[0, 255]。；src_stride(输入): 源操作数X轴方向前一个分形起始地址与后一个分形起始地址的间隔，单位为32B。；dst_stride(输入): 目的操作数X轴方向前一个分形起始地址与后一个分形起始地址。

约束：- 各存储单元的空间大小和对齐要求
- scale矩阵的分形固定为(16, 2, 16)，对应L0A Buffer的分形为(16, 32, 16)，占L0A Buffer地址的1 / 16，需要按照这种地址约束存放地址。
- dst（L0A Buffer的地址）的数据类型支持fp4x2_e2m1_t、fp4x2_e1m2_t、fp8_e5m2_t、fp8_e4m3fn_t，src的数据类型支持fp8_e8m0_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12l0aTrans](asc_copy_l12l0a_trans.md)（`related`）：MX 量化路径还需专用 scale/格式处理，不由普通 Trans 隐式完成。
- [AscMmadMx](../cube_compute/asc_mmad_mx.md)（`related`）：《AscMmadMx》说明完成带量化系数的矩阵乘加计算（MmadMx），左矩阵A和右矩阵B分别配有量化系数矩阵ScaleA和ScaleB，按K维度每32个元素共享一个量化系数。；《AscCopyL12l0aMx》说明将Mx scale矩阵从L1 Buffer搬运到L0A Buffer。。二者在AscMmadMx消费A/B量化系数矩阵；Mx搬入、SetTensorScaleA/B和MxMatmul场景构成完整数据合同上存在可执行的直接衔接。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md)（`related`）：MX 量化矩阵路径有专用 L0A 搬运语义，不能以普通 L12L0A 代替 scale/格式处理。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyL12l0aMx》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`same_topic`）：asc_copy_l12l0a 与《AscCopyL12l0aMx》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
<!-- cannbot:related:end -->
