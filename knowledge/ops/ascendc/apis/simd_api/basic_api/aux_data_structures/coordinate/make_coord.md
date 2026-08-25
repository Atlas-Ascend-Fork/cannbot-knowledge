---
type: API
title: MakeCoord
description: 将传入的数据打包成Coord数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/MakeCoord.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# MakeCoord

构造Coordinate坐标结构体。支持传入最多8个维度的坐标值，从高维到低维依次排列。

函数原型提供2维到8维的构造重载。参数为各维度的坐标值（uint32_t）。返回Coordinate结构体。用于创建多维索引坐标。

<!-- cannbot:related:start -->
## 相关

- [Coord（基础API）](../../data_structure_tensor_api/layout_structure/coord.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；MakeCoord正文说明“将传入的数据打包成Coord数据结构”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [MakeShape](../layout/make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeCoord》说明将传入的数据打包成Coord数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Coordinate](coordinate.md)（`same_topic`）：MakeCoord 与《Coordinate》的实质衔接是：MakeCoord 构造最多八维 Coordinate，Crd2Idx 再结合 Layout 把坐标映射为线性索引；另一 Coord 构造入口用于区分两套数据结构。
- [Coordinate简介](coordinate_intro.md)（`same_topic`）：MakeCoord 把最多八维坐标打包为 Coordinate，是坐标对象进入后续索引计算的构造入口。
- [Crd2Idx](crd2_idx.md)（`same_topic`）：Crd2Idx 与《MakeCoord》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [MakeCoord](../../data_structure_tensor_api/layout_structure/make_coord.md)（`same_topic`）：MakeCoord：MakeCoord返回 Coord对象；TensorAPI Coord与辅助数据结构 MakeCoord描述两套可互查的坐标构造契约，避免把坐标与Shape/Layout构造混用。 目标卡《MakeCoord》补充：将传入的数据打包成Coord数据结构。
<!-- cannbot:related:end -->
