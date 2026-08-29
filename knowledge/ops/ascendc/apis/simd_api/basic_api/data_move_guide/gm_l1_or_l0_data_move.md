---
type: API
title: GmL1OrL0DataMove
description: 提供Global Memory与L1 Buffer及L0 Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及矩阵计算结果搬出等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/GM_L1_or_L0_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GmL1OrL0DataMove

Global Memory 与 L1 Buffer/L0 Buffer 间数据搬运接口概述。GM↔L1 支持 DataCopy（连续/高维切分/ND2NZ/DN2NZ 随路转换）、DataCopyPad（非对齐）、LoadData（2D/2DV2 矩阵搬运）。GM→L0A/L0B 支持 LoadData（2D 分形搬运）。L0C→GM 支持 DataCopy 和 Fixpipe（随路量化/ReLU/格式转换）。DataBlock（32B）为基本寻址粒度，count×sizeof(T) 须 32B 对齐。具体接口详见 cube_compute_ISASI 章节。
