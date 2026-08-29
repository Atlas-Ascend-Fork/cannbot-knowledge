---
type: API
title: 数据通路（概述）
description: AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_path.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 数据通路（概述）

AI Core 含 Cube/Vector/Scalar 计算单元和分层存储：GM→L1 Buffer→L0A/L0B/L0C Buffer→UB→BiasTable/Fixpipe Buffer。搬运引擎：MTE2（GM→Local）、MTE3（Local→GM）、MTE1（L1→L0）、FixPipe（L0C→GM 带随路量化/激活）。同一物理内存可映射多个 TPosition（如 UB 映射 VECIN/VECCALC/VECOUT）。

NPU 架构版本 3510（950）变化：新增 L0C→UB 和 UB→L1 通路；删除 GM→L0A/L0B 和 L1→GM 直连通路。
