---
type: API
title: GetReduceRepeatMaxMinSpr
description: 获取ReduceRepeat或ReduceMax/ReduceMin计算的最值及索引，结果以全局变量形式存储。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute_aux_config/GetReduceRepeatMaxMinSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# GetReduceRepeatMaxMinSpr

获取ReduceRepeat或ReduceMax/ReduceMin计算的最值及索引，结果以全局变量形式存储。

ReduceRepeat接口用于对每个repeat内所有数据进行归约操作，根据模板参数reduceType进行求和/求最大值/求最小值操作，结果按顺序写入目标地址。 在求最大值或最小值时可以返回对应的索引，返回的索引值为每个repeat内部索引。支持高维切分计算。 图1 ReduceRepeat计算示意图

本接口组包含 ReduceRepeat<MAX/MIN>, ReduceMax, ReduceMin, ReduceRepeat<MAX/MIN>, ReduceMax。

本接口属于 UB 矢量计算归约接口。

约束：操作数地址重叠约束请参考通用地址重叠约束。；源操作数的地址对齐约束请参考通用地址对齐约束，起始地址需要32字节对齐；目的操作数的起始地址对齐约束受操作数数据类型、reduceType和order参数的影响，请参考表3。；

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
