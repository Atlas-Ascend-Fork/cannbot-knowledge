---
type: API
title: Coordinate简介
description: Coordinate本质上是一个元组（tuple），用于表示张量在不同维度的位置信息，即坐标值。Coordinate（坐标）和Layout（布局）、Index（内存位置索引）之间存在紧密的关联：
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/Coordinate_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Coordinate简介

Coordinate是用于描述Tensor多维索引的坐标结构体，支持最多8维坐标。通过MakeCoord构造，可用于Tensor的元素索引和位置计算。坐标维度从高到低依次对应Tensor的维度。

Coordinate与Crd2Idx配合使用：Crd2Idx将坐标转换为线性索引，用于在Tensor中定位元素。

<!-- cannbot:related:start -->
## 相关

- [Crd2Idx](crd2_idx.md)（`related`）：Crd2Idx 消费 Coordinate 和布局信息得到线性偏移，直接把多维坐标结构落实为 Tensor 访存位置。
- [Layout简介](../layout/layout_intro.md)（`related`）：Layout 提供 Shape 和 Stride，正是 Crd2Idx 将 Coordinate 线性化所需的内存排布语义。
- [MakeCoord](make_coord.md)（`same_topic`）：MakeCoord 把最多八维坐标打包为 Coordinate，是坐标对象进入后续索引计算的构造入口。
<!-- cannbot:related:end -->
