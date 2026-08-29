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

<!-- cannbot:related:start -->
## 相关

- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：“L1/L0A/L0B/L0C 的正确构造方式是带 `TPosition` 的构造函数 `LocalTensor<T>(TPosition pos, uint32_t addr, uint32_t tileSize)`，由 `TPosition`（`A1`=L1A、`A2`=L0A、`B2`=L0B、`CO1`=L0C）承担位置语义，裸类型无需具备 trait。”；“TPosition是Tensor位置枚举，描述Tensor在Ascend AI Core存储层次中的位置。包含VECIN（输入队列位置）、VECCALC（中间计算位置）、VECOUT（输出队列位置）、TSCN（L1 Buffer位置）、LCM（L0C Buffer位置）等。”。Runbook把 TPosition 的抽象位置合同落到 arch35 L1/L0 LocalTensor 构造修法，并给出 SetAddr 与裸地址构造的失败信号。
- [GetPosition](../data_structures/local_tensor/get_position.md)（`related`）：返回值为 TPosition 枚举，支持 VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2 等逻辑位置。；TPosition是Tensor位置枚举，描述Tensor在Ascend AI Core存储层次中的位置。前者返回后者定义的枚举，直接用于按存储位置分派逻辑。
<!-- cannbot:related:end -->
