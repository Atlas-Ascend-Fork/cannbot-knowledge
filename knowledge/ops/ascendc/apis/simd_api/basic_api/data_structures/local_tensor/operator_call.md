---
type: API
title: operator
description: 获取本LocalTensor的第offset个变量的引用。用于左值，相当于SetValue接口，用于右值，相当于GetValue接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# operator

获取本LocalTensor的第offset个变量的引用。用于左值，相当于SetValue接口，用于右值，相当于GetValue接口。

设置LocalTensor中的某个值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。

本接口组包含 SetValue，辅助接口包括 GetValue。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

约束：不要大量使用SetValue对LocalTensor进行赋值，会使性能下降。若需要大批量赋值，请根据实际场景选择数据填充基础API接口或数据填充高阶API接口（Pad、Broadcast），以及在需要生成递增数列的场景，选择Arange。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
