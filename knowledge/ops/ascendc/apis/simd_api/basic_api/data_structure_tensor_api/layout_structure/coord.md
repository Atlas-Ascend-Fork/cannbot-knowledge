---
type: API
title: Coord（基础API）
description: 定义张量逻辑坐标，并配合 Layout 完成多维坐标到线性内存索引的映射。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Coord.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Coord（基础API）

Coord 用于定义张量的逻辑坐标，配合 Layout 实现逻辑坐标到一维内存地址的映射。头文件为 tensor_api/tensor.h。
Coord 通过 Std::tuple 的可变参数模板 Coords 定义各维度坐标，需使用 MakeCoord 构造实例。
作为参数传入 Layout 的 operator() 成员函数可完成坐标到索引的映射，传入 Tensor 的 Slice 接口可实现张量偏移与切片。
还可通过 Crd2Idx 接口将多维坐标转换为线性坐标。本接口为试验接口，后续版本可能调整，不保证兼容性。仅 Ascend 950PR/950DT 支持。
