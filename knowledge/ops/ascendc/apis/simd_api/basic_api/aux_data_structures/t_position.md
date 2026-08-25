---
type: API
title: TPosition
description: Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TPosition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# TPosition

TPosition是Tensor位置枚举，描述Tensor在Ascend AI Core存储层次中的位置。包含VECIN（输入队列位置）、VECCALC（中间计算位置）、VECOUT（输出队列位置）、TSCN（L1 Buffer位置）、LCM（L0C Buffer位置）等。

TPosition用于LocalTensor和GlobalTensor的类型区分，不同位置的Tensor有不同的访问特性。在InitBuffer时通过TPosition指定队列类型。
