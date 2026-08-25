---
type: API
title: Coordinate
description: Coordinate 辅助数据结构用于描述张量坐标，提供 MakeCoord 构造与 Crd2Idx 坐标到索引转换接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/Coordinate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Coordinate

Coordinate 辅助数据结构用于描述张量坐标，提供 MakeCoord 构造与 Crd2Idx 坐标到索引转换接口。

将传入的数据打包成Coord数据结构。

本接口组包含 MakeCoord, Crd2Idx。

本接口属于 Tensor 数据结构操作接口。

返回值：Coord结构类型（Std::tuple类型的别名）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
