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

- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：焦点处理TPosition 在 Tensor 和队列中的片上位置类型约束；L1/L0 tensor 须用 TPosition 构造非 SetAddr正文界定“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr,”。候选直接读取/构造 TPosition 或复现 TPosition 枚举和 L1/L0 Tensor 构造错误。
- [TQue 位置参数须用 AscendC::TPosition 枚举](../../../../runbooks/compilation/tque_ascendc_tposition.md)（`exemplifies`）：TQue 位置参数须用 AscendC::TPosition 枚举 与《TPosition》的实质衔接是：TPosition定义了TQue/LocalTensor位置枚举；L1/L0 构造案例和 GetPosition 分别给出相同位置契约的创建与读取方式。
- [GetPosition](../data_structures/local_tensor/get_position.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《TPosition》明确提供“Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
<!-- cannbot:related:end -->
