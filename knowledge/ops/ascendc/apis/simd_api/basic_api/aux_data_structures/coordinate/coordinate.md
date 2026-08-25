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

<!-- cannbot:related:start -->
## 相关

- [Coord（基础API）](../../data_structure_tensor_api/layout_structure/coord.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Coordinate正文说明“Coordinate 辅助数据结构用于描述张量坐标，提供 MakeCoord 构造与 Crd2Idx 坐标到索引转换接口”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Crd2Idx](crd2_idx.md)（`same_topic`）：Crd2Idx 与《Coordinate》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [Layout（辅助数据结构）](../layout/layout.md)（`same_topic`）：Coordinate 与《Layout（辅助数据结构）》的实质衔接是：Coordinate 由 MakeCoord 构造，并由 Crd2Idx 结合 Layout 的 shape/stride 转成线性索引。
- [MakeCoord](make_coord.md)（`same_topic`）：MakeCoord 与《Coordinate》的实质衔接是：MakeCoord 构造最多八维 Coordinate，Crd2Idx 再结合 Layout 把坐标映射为线性索引；另一 Coord 构造入口用于区分两套数据结构。
<!-- cannbot:related:end -->
