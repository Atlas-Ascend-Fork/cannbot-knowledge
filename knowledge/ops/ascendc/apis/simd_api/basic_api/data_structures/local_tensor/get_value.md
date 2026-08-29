---
type: API
title: GetValue
description: 获取LocalTensor指定索引的数值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetValue

获取 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`exemplifies`）：焦点卡只定义“获取 LocalTensor 指定索引的元素值。”，候选卡实测“`PipeBarrier<PIPE_V>` 只约束 Vector pipe 内部顺序，不能保证前一 VF 的 `StoreAlign` 已对 `__aicore__` 标量侧 `LocalTensor::GetValue` 可见”；该 runbook 给出使用 GetValue 时最关键的跨域可见性故障与替代方案。
<!-- cannbot:related:end -->
