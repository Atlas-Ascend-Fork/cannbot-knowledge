---
type: API
title: UnaryRepeatParams
description: UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/UnaryRepeatParams.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# UnaryRepeatParams

一元计算接口的重复参数结构体，用于描述单操作数指令（如Exp、Sin等）的源操作数和目的操作数的步长、block偏移等参数。

包含源操作数src的blockStride（每个block间偏移）、src的repeatStride（每次repeat间偏移）、目的操作数dst的blockStride和repeatStride等字段。通过UnaryRepeatParams构造或直接传入参数。
