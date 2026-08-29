---
type: API
title: LoadDataWithTranspose
description: 完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadDataWithTranspose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# LoadDataWithTranspose

将数据从L1 Buffer搬运到L0A或L0B Buffer，支持在搬运过程中执行转置操作。用于需要在数据搬入时改变矩阵行列排布的场景。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、loadDataParams（含转置配置和各维度切分信息）。约束：遵循Cube计算地址对齐和转置约束。

<!-- cannbot:related:start -->
## 相关

- [Cube计算(ISASI)总体说明](overall_description.md)（`related`）：“将数据从L1 Buffer搬运到L0A或L0B Buffer，支持在搬运过程中执行转置操作。用于需要在数据搬入时改变矩阵行列排布的场景。”描述通用目的端，而“Ascend 950PR/950DT 删除了 GM 到 L0A/L0B 的直连通路，需拆分为 GM→L1→L0A/L0B 两步搬运；该型号下 LoadDataWithTranspose 仅支持 L1→L0B 通路。”补上 950 的关键收窄；联合阅读可避免在 950 选择 L0A 目的端。
<!-- cannbot:related:end -->
