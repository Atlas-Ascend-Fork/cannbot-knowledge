---
type: API
title: AscSetGm2l1Pad
description: 设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_gm2l1_pad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSetGm2l1Pad

将数据从Global Memory (GM)非对齐搬运到L1 Buffer时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值。

参数：pad_val(输入): 左右两侧需要填补的数据值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2L1Nd2Nz](asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md)（`related`）：AscSetGm2l1Pad说明设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值。
- [AscSetGm2l1Loop1Stride](asc_set_gm2l1_loop1_stride.md)（`related`）：《AscSetGm2l1Pad》明确“设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值。”；它与《AscSetGm2l1Loop1Stride》的“设置GM到L1搬运时内层循环中相邻迭代数据块间的间隔。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscCopyGm2l1Align](asc_copy_gm2l1_align.md)（`same_topic`）：焦点处理GM→L1 对齐搬运及其 loop stride、size、padding 配置；AscSetGm2l1Pad正文说明“设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值”。候选直接配置或执行同一 GM→L1 搬运，明确对齐版与格式转换版的选择。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetGm2l1Pad》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
<!-- cannbot:related:end -->
