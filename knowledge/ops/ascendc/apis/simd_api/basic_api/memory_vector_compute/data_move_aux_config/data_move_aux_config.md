---
type: API
title: 数据搬运辅助配置接口
description: 矢量数据搬运辅助配置接口集，包含 NdDmaDci、SetPadValue(ISASI)、SetLoopModePara、ResetLoopModePara 等。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/data_move_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据搬运辅助配置接口

Memory 矢量数据搬运的辅助配置接口集合。NdDmaDci 用于配置 ND 格式 DMA 搬运参数；SetPadValue(ISASI) 设置搬运时的填充值；SetLoopModePara/ResetLoopModePara 设置与重置循环搬运模式参数。这些接口在调用 DataCopy 等搬运接口前配置，用于控制搬运行为。

<!-- cannbot:related:start -->
## 相关

- [NdDmaDci](nd_dma_dci.md)（`related`）：NdDmaDci 配置 NDDMA 的数据压缩信息，是 DataMoveAuxConfig 下的具体搬运控制项。
- [ResetLoopModePara](reset_loop_mode_para.md)（`related`）：ResetLoopModePara 清除循环搬运配置，是 DataMoveAuxConfig 管理状态的复位操作。
- [SetLoopModePara](set_loop_mode_para.md)（`related`）：SetLoopModePara 设置循环搬运参数，与 ResetLoopModePara 构成状态启用和复位的完整调用链。
- [SetPadValue](set_pad_value_isasi.md)（`related`）：SetPadValue 写入 DataCopyPad 使用的填充值，属于搬运辅助配置的直接子能力。
<!-- cannbot:related:end -->
