---
type: API
title: GetPosition
description: 获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetPosition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetPosition

获取 LocalTensor 所在的 TPosition 逻辑位置。函数签名为 __aicore__ inline int32_t GetPosition() const，无入参。
返回值为 TPosition 枚举，支持 VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2 等逻辑位置。
用于在运行时查询 Tensor 所处的缓冲区位置，从而选择不同的处理逻辑。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [TPosition](../../aux_data_structures/t_position.md)（`related`）：返回值为 TPosition 枚举，支持 VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2 等逻辑位置。；TPosition是Tensor位置枚举，描述Tensor在Ascend AI Core存储层次中的位置。前者返回后者定义的枚举，直接用于按存储位置分派逻辑。
<!-- cannbot:related:end -->
