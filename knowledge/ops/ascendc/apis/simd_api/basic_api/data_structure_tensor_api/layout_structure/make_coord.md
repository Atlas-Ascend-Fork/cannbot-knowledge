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

<!-- cannbot:related:start -->
## 相关

- [Coord（基础API）](coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；MakeCoord正文说明“需要包含的头文件为：#include "tensor_api/tensor.h"。 构造Coord对象，用于定义张量的坐标”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [MakeCoord](../../aux_data_structures/coordinate/make_coord.md)（`same_topic`）：MakeCoord：MakeCoord返回 Coord对象；TensorAPI Coord与辅助数据结构 MakeCoord描述两套可互查的坐标构造契约，避免把坐标与Shape/Layout构造混用。 目标卡《MakeCoord》补充：将传入的数据打包成Coord数据结构。
- [Slice（基础API）](../tensor_structure/slice.md)（`same_topic`）：Slice（基础API） 与《MakeCoord》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
<!-- cannbot:related:end -->
