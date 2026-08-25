---
type: API
title: AscSetL13dSize
description: 设置3D搬运接口在L1 Buffer的边界值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l13d_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscSetL13dSize

设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口在L1 Buffer的边界值。

参数：value(输入): 用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口在L1 Buffer的边界值，单位是字节。非0场景的边界值不能小于。

约束：- 需配合asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口使用。
- 如果使用asc_set_l13d_size接口设置了边界值，asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的L1 Buffer初始地址要在设置的边界内（value）。
- 如果asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的源操作数在L1 Buffer上的地址超出设置的边界值（value），则会从L1 Buffer起始地址开始读取数据。
- 操作数地址对齐约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dFmatrix](asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscSetL13dSize》具体提供“设置3D搬运接口在L1 Buffer的边界值。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_arch_2201.md)（`related`）：AscSetL13dSize 设置的 L1 三维边界由 2201 路径的 AscCopyL12L0A 三维搬运使用，前者是后者的配置前置条件。
- [asc_copy_l12l0b](asc_copy_l12l0b/asc_copy_l12l0b_arch_2201.md)（`related`）：AscSetL13dSize 设置的 L1 三维边界由 2201 路径的 AscCopyL12L0B 三维搬运使用，前者是后者的配置前置条件。
- [AscCopyL12l0bMx](asc_copy_l12l0b_mx.md)（`same_topic`）：AscCopyL12l0bMx 与《AscSetL13dSize》的实质衔接是：AscCopyL12l0bMx 是 Mx scale 的 L1→L0B 路径；L0A 对应入口、普通/稀疏 L0B、GM→L1、3D 配置和 AscMmadMx 共同构成 Mx 矩阵计算链。
- [AscSetL13dRpt](asc_set_l13d_rpt.md)（`same_topic`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscSetL13dSize》明确提供“设置3D搬运接口在L1 Buffer的边界值。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
<!-- cannbot:related:end -->
