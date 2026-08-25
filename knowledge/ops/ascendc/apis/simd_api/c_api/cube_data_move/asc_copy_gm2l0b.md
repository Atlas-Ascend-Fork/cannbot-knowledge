---
type: API
title: AscCopyGm2l0b
description: 将矩阵数据从GM搬运到L0B Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l0b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyGm2l0b

将矩阵数据从Global Memory搬运到L0B Buffer。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；base_idx(输入): 以16*16个数对矩阵进行分块，搬运的起始分块ID。；repeat(输入): 迭代次数。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分形起始地址的间隔。；dst_gap(输入): 相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。

约束：- 各存储单元的空间大小和对齐要求

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1](asc_copy_gm2l1/asc_copy_gm2l1.md)（`related`）：AscCopyGm2L1 提供先从 GM 搬到 L1 的通用阶段，可与 L1→L0B 组合替代不支持的 GM→L0B 直达通路。
- [AscCopyGm2l0a](asc_copy_gm2l0a.md)（`related`）：AscCopyGm2l0a 与 AscCopyGm2l0b 分别把 Matmul 左、右操作数从 GM 直接加载到 L0A/L0B，block 与 stride 契约对称。
- [AscCopyL12L0b](asc_copy_l12l0b/asc_copy_l12l0b.md)（`related`）：AscCopyL12L0b 是 GM 数据先进入 L1 后搬入 L0B 的第二段，与 AscCopyGm2l0b 的直达路径构成 B 矩阵搬入路线对照。
- [AscSetL13dRpt](asc_set_l13d_rpt.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscCopyGm2l0b》明确提供“将矩阵数据从GM搬运到L0B Buffer。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscCopyGm2l0b》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
<!-- cannbot:related:end -->
