---
type: API
title: 归约计算辅助配置接口
description: 归约计算辅助配置接口索引页，包含GetReduceRepeatSumSpr与GetReduceRepeatMaxMinSpr(ISASI)。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute_aux_config/reduction_compute_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 归约计算辅助配置接口

归约计算辅助配置接口索引页，包含GetReduceRepeatSumSpr与GetReduceRepeatMaxMinSpr(ISASI)。

获取ReduceSum接口的计算结果，仅支持tensor前n个数据连续计算接口使用。计算结果以全局变量形式存储，可以随时调用获取。

本接口属于 UB 矢量计算归约接口。

返回值：ReduceSum接口的计算结果。

约束：仅支持配合ReduceSum的tensor前n个数据连续计算接口使用。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
