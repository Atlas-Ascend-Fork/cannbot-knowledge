---
type: API
title: AscCopyL12L0bTrans
description: 将数据从L1 Buffer搬运到L0B Buffer并支持转置的接口，包含不同架构版本的具体实现。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b_trans/asc_copy_l12l0b_trans.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# asc_copy_l12l0b_trans

- **asc_copy_l12l0b_trans_arch_2201**

- **asc_copy_l12l0b_trans_arch_3510**

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12L0b](../asc_copy_l12l0b/asc_copy_l12l0b.md)（`related`）：普通 B 搬运不转置，按源布局选择。
- [AscCopyL12l0aTrans](../asc_copy_l12l0a_trans.md)（`related`）：L0B Trans 处理右矩阵，L0A Trans 处理左矩阵，操作数侧别不可混用。
- [AscSetL13dFmatrix](../asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscCopyL12L0bTrans》具体提供“将数据从L1 Buffer搬运到L0B Buffer并支持转置的接口，包含不同架构版本的具体实现。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscCopyL12L0bTrans](asc_copy_l12l0b_trans_arch_2201.md)（`same_topic`）：总页与 2201 变体共同定义转置 B 搬运。
- [AscCopyL12L0bTrans](asc_copy_l12l0b_trans_arch_3510.md)（`same_topic`）：3510 变体给出 Ascend950 签名。
<!-- cannbot:related:end -->
