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

- [AscCopyL12L0a](asc_copy_l12l0a.md)（`same_topic`）：“asc_copy_l12l0a_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品”与“本接口不支持2D格式搬运的转置场景”把总览的平台选择落到 2201 版本的能力边界。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_3510.md)（`same_topic`）：“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。”与“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里。包含2D格式搬运、3D格式搬运。”分别来自双方当前正文。两卡覆盖同一 L1→L0A 512B 分形搬运，但 3510 增加 2D 转置路线，2201 明确不支持该转置；跨平台移植时必须联合核对。
<!-- cannbot:related:end -->
