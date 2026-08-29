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
