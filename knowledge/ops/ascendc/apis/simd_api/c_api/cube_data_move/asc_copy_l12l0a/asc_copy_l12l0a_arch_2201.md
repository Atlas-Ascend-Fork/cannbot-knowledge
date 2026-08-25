---
type: API
title: asc_copy_l12l0a
description: 用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_l12l0a

用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。

参数：dst(输出): 目的L0A Buffer地址。；src(输入): 源L1 Buffer地址。；start_index(输入): 分形矩阵ID，说明搬运起始位置为源操作数中第几个分形（0为源操作数中第1个分形矩阵）。取值范围：[0, 65535]。单位为512字节。；repeat(输入): 迭代次数，每个迭代可以处理512B数据。取值范围：[1, 255]。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分型起始地址的间隔。取值范围：[0, 65535]。单位为512字节。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。取值范围：[0, 65535]。单位为512字节。；dst(输出): 目的L0A Buffer地址。；src(输入): 源L1 Buffer地址。

约束：- 各存储单元的空间大小和对齐要求
- 本接口不支持2D格式搬运的转置场景。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12l0aMx](../asc_copy_l12l0a_mx.md)（`related`）：MX 量化矩阵路径有专用 L0A 搬运语义，不能以普通 L12L0A 代替 scale/格式处理。
- [AscCopyL12l0aTrans](../asc_copy_l12l0a_trans.md)（`related`）：需要转置布局时应使用 L12L0A Trans 变体，而普通接口不隐式转置。
- [AscSetL13dPadding](../asc_set_l13d_padding.md)（`related`）：《asc_copy_l12l0a》明确“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscSetL13dSize](../asc_set_l13d_size.md)（`related`）：AscSetL13dSize 设置的 L1 三维边界由 2201 路径的 AscCopyL12L0A 三维搬运使用，前者是后者的配置前置条件。
- [AscSetL3dRptB](../../sys_var/asc_set_l3d_rpt_b.md)（`related`）：“AscSetL3dRptB”定义：设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。；“asc_copy_l12l0a”定义：用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。。实质衔接：AscSetL3dRptB 配置 L1→L0A/L0B 2D repeat，SetL13dRpt 是相关 Load3D repeat 配置，真正消费者是 2201 的 asc_copy_l12l0a。
- [asc_copy_l12l0b](../asc_copy_l12l0b/asc_copy_l12l0b_arch_2201.md)（`related`）：L0A 和 L0B 分别承载矩阵 A/B；源同为 L1，但目标和布局需与操作数侧别一致。
- [AscCopyL12L0a](asc_copy_l12l0a.md)（`same_topic`）：总页定义 L1→L0A 搬运语义，2201 页给出该架构的签名与限制。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_3510.md)（`same_topic`）：asc_copy_l12l0a 与《asc_copy_l12l0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
<!-- cannbot:related:end -->
