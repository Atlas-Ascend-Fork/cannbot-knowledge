---
type: API
title: asc_storeunalign_postupdate
description: 该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。
  该接口每调用一次接口会更新目的操作数在UB上的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_postupdate_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_storeunalign_postupdate

该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。
函数原型：void asc_storeunalign_postupdate(__ubuf__ int8_t* dst, vector_store_unalign& src0, vector_int8_t src1)
约束：该接口中的dst不需要32B对齐。；本接口应该配合asc_storeunalign_post接口一起使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
