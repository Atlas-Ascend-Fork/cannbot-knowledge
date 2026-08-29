---
type: API
title: AscSetL0cCopyPrequant
description: 设置数据搬运随路量化流程中的标量量化参数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l0c_copy_prequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL0cCopyPrequant

数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的标量量化参数。

参数：config(输入): 量化过程中使用到的标量量化参数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的标量量化参数。；将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。；AscSetL0CCopyPreQuant 配置搬运随路量化使用的标量参数，AscCopyL0c2Gm 则在 L0C 到 GM 搬运中执行该随路量化能力，前者直接支撑后者的量化路径。
<!-- cannbot:related:end -->
