---
type: API
title: 数据结构
description: SIMD C API数据结构汇总，包含填充值配置、3D矩阵加载配置、多维padding配置及原子存储配置等结构体定义。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/data_structures.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据结构

SIMD C API数据结构汇总，提供搬运和计算接口的配置结构体。asc_fill_value_config配置填充值，asc_ndim_pad_count_config配置多维padding参数，asc_store_atomic_config配置原子存储属性。
asc_load3d_v2_config配置3D数据加载参数，asc_l13d_fmatrix_config配置L1到3D矩阵的格式参数。各结构体用于对应接口的入参传递和行为控制。
