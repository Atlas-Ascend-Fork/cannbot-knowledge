---
type: API
title: OperatorSubscript
description: 获取距原LocalTensor起始地址偏移量为offset的新LocalTensor，offset不能超过原有LocalTensor的size大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# OperatorSubscript

获取距原 LocalTensor 起始地址偏移量为 offset 的新 LocalTensor，offset 不能超过原 LocalTensor 的 size 大小。
通过 operator 下标操作符获取偏移 Tensor，参数 offset 为 uint32_t 类型偏移量，单位为元素，返回值为偏移后的新 LocalTensor，共享原 Tensor 的存储空间。
常用于对 LocalTensor 进行分段操作，例如 inputLocal 偏移 16 个元素后返回的新 Tensor 可供 Add 等计算接口使用。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。
