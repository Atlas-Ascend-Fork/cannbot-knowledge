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
