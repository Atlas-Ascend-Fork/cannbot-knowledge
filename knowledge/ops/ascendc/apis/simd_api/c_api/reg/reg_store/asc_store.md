---
type: API
title: AscStore
description: 从矢量数据寄存器搬出数据到UB，不区分是否对齐，对齐场景推荐使用asc_storealign接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStore

reg计算数据搬运接口，适用于从矢量数据寄存器搬出到UB的场景，不区分是否对齐，在追求极致性能时，对齐场景推荐使用asc_storealign接口。
函数原型：void asc_store(__ubuf__  int8_t* dst, vector_int8_t src)
约束：count的取值范围为[1, VL/sizeof(dst)]，VL为矢量长度。超出该范围会导致未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
