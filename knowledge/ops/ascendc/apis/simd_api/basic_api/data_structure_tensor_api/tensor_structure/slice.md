---
type: API
title: Slice（基础API）
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/Slice.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Slice（基础API）

从张量指定坐标处切出子张量。根据起始坐标 coord 和切片描述信息 info 计算新起始位置，构造子张量，保持与原张量相同的存储位置类型。头文件 `tensor_api/tensor.h`。仅 950 支持。
