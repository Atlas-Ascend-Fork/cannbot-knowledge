---
type: API
title: GmUbDataMove
description: 提供Global Memory与Unified Buffer间数据搬运接口概述，支持连续搬运、高维切分、切片搬运、格式转换及非对齐搬运等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/GM_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GmUbDataMove

Global Memory 与 Unified Buffer 间数据搬运接口概述。GM→UB 支持 DataCopy（连续/高维切分/切片/ND2NZ/NDDMA 多维搬运）、DataCopyPad（非对齐）。UB→GM 支持 DataCopy（连续/高维切分/切片/NZ2ND）、DataCopyPad。UB→GM 的 CO2→GM 通路仅 Atlas 推理 AI Core 支持。切片搬运和部分随路转换为软仿接口。DataBlock（32B）为基本寻址粒度。
