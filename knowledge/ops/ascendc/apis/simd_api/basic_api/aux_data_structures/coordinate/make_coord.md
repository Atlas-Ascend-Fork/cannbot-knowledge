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

- [Coordinate简介](coordinate_intro.md)（`related`）：通过MakeCoord构造，可用于Tensor的元素索引和位置计算。；构造Coordinate坐标结构体。；简介给出的 Coordinate 生产步骤由 MakeCoord 的构造合同具体实现。
- [Crd2Idx](crd2_idx.md)（`related`）：将Coordinate坐标转换为Tensor中的线性索引（index）；构造Coordinate坐标结构体。MakeCoord 生成 Crd2Idx 的 Coordinate 输入，Crd2Idx 再结合 shape 计算线性偏移；联合阅读即可完成从多维坐标构造到 Tensor 索引的调用链。
<!-- cannbot:related:end -->
