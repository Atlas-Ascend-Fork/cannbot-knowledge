---
type: API
title: L1OrL0CUbDataMove
description: 提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_or_L0C_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1OrL0CUbDataMove

L1 Buffer 及 L0C Buffer 与 Unified Buffer 间数据搬运接口概述。L1→UB 支持 DataCopyL1ToUB（连续/高维切分，仅 950）。L0C→UB 支持 DataCopy（增强随路反量化/ReLU，仅 Atlas 推理 AI Core）和 Fixpipe（随路量化/格式转换，950/Atlas 200I/500 A2）。UB→L1 支持 DataCopy（连续/高维切分/ND2NZ，a2/a3/950）。UB 地址需 32B 对齐。
