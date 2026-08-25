---
type: API
title: asc_copy_l12l0b
description: 用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里。包含2D格式搬运、3D格式搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b/asc_copy_l12l0b_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_l12l0b

用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里。包含2D格式搬运、3D格式搬运。

参数：dst(输出): 目的L0B Buffer地址。；src(输入): 源L1 Buffer地址。；start_index(输入): 分形矩阵ID，说明搬运起始位置为源操作数中第几个分形（0为源操作数中第1个分形矩阵）。取值范围：[0, 65535]。单位为512字节。；repeat(输入): 迭代次数，每个迭代可以处理512B数据。取值范围：[1, 255]。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分形起始地址的间隔。取值范围：[0, 65535]。单位为512字节。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。取值范围：[0, 65535]。单位为512字节。；dst(输出): 目的L0B Buffer地址。；src(输入): 源L1 Buffer地址。

约束：- 各存储单元的空间大小和对齐要求
- 本接口不支持2D格式搬运的转置场景，若要实现

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dSize](../asc_set_l13d_size.md)（`related`）：AscSetL13dSize 设置的 L1 三维边界由 2201 路径的 AscCopyL12L0B 三维搬运使用，前者是后者的配置前置条件。
- [asc_copy_l12l0a](../asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md)（`related`）：L0A 和 L0B 分别承载矩阵 A/B；源同为 L1，但目标和布局需与操作数侧别一致。
- [AscCopyL12l0bMx](../asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《asc_copy_l12l0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [asc_copy_l12l0b](asc_copy_l12l0b_arch_3510.md)（`same_topic`）：两卡执行同一 L1→L0B 512B 矩阵搬运；3510 版本增加 2D 转置并改用 M/K 起点与步长参数，2201 版本则无转置，迁移时必须按架构重建参数。
<!-- cannbot:related:end -->
