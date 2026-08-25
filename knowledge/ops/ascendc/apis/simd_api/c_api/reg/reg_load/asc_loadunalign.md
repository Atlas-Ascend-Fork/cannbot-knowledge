---
type: API
title: AscLoadunalign
description: 从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadunalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadunalign

reg计算数据搬运接口，适用于从UB非32B对齐的起始地址连续搬入矢量数据寄存器的场景。 该接口不改变源操作数在UB上的地址，每次循环的调用都需要用户手动更新源操作数在UB上的地址。
函数原型：void asc_loadunalign(vector_int8_t& dst, vector_load_unalign& src0, __ubuf__ int8_t *src1)
约束：该接口中的src1不需要32B对齐。；调用该接口之前，需要调用asc_loadunalign_pre进行非对齐搬入前的初始化。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
