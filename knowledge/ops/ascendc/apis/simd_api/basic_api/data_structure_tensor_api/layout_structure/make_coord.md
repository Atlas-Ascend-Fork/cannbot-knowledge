---
type: API
title: MakeCoord
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 构造Coord对象，用于定义张量的坐标。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeCoord.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MakeCoord

需要包含的头文件为：#include "tensor_api/tensor.h"。 构造Coord对象，用于定义张量的坐标。

需要包含的头文件为：#include "tensor_api/tensor.h"。 构造Coord对象，用于定义张量的坐标。

返回值：返回Coord 对象。

约束：各维度的坐标值需为非负整数。；参数数量必须与对应的Shape维度数量一致。

支持的硬件型号：Ascend 950PR/Ascend 950DT。
