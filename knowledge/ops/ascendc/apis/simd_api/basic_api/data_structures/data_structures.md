---
type: API
title: 数据结构
description: AscendC 矢量计算基础 API 数据结构总览，涵盖内置数据类型、精度转换、LocalTensor、GlobalTensor。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/data_structures.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据结构

AscendC 矢量计算基础 API 的数据结构总览，涵盖内置数据类型、精度转换接口，以及 LocalTensor（UB 侧局部张量）和 GlobalTensor（GM 侧全局张量）两类核心张量结构。LocalTensor/GlobalTensor 提供构造、缓冲区设置、元素读写、形状查询、类型重解释等能力，是矢量与 Cube 计算数据传递的基础。
