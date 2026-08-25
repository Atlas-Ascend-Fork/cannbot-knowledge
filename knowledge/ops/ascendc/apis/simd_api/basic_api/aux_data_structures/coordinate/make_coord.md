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
