---
type: API
title: AscCopyGm2l0a
description: 将数据从GM搬运到L0A Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l0a.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyGm2l0a

将数据从GM搬运到L0A Buffer。

参数：dst(输出): 目的操作数起始地址。；src(输入): 源操作数起始地址。；base_idx(输入): 分形矩阵ID，搬运起始位置为源操作数的第几个分形（0为源操作数中第1个分形矩阵）。取值范围：[0, 65535]。；repeat(输入): 迭代次数，每个迭代可以处理512B数据。取值范围：[1, 255]。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分形起始地址的间隔，单位：512B。取值范围：[0, 65535]。；dst_gap(输入): 相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。单位：512B。取值范围：[0, 65535]。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l0b](asc_copy_gm2l0b.md)（`related`）：AscCopyGm2l0a 与 AscCopyGm2l0b 分别把 Matmul 左、右操作数从 GM 直接加载到 L0A/L0B，block 与 stride 契约对称。
- [AscCopyL12L0a](asc_copy_l12l0a/asc_copy_l12l0a.md)（`related`）：AscCopyL12L0A 提供先 GM→L1 再 L1→L0A 的分级加载替代路径，可据存储位置选择与直接 GM→L0A 的接口。
- [AscSetL13dRpt](asc_set_l13d_rpt.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyGm2l0a》明确提供“将数据从GM搬运到L0A Buffer。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`related`）：asc_copy_l12l0a 与《AscCopyGm2l0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
<!-- cannbot:related:end -->
