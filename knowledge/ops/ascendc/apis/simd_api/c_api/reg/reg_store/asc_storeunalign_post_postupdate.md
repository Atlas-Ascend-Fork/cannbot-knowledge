---
type: API
title: asc_storeunalign_post_postupdate
description: 从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，每调用一次自动更新目的地址，将非对齐寄存器中暂存的尾块搬出到UB，需在asc_storeunalign_postupdate之后调用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_post_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_storeunalign_post_postupdate

reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的尾块场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。 需要先调用下列接口后，再调用本接口。
函数原型：void asc_storeunalign_post_postupdate(__ubuf__  int8_t*& dst, vector_store_unalign src, int32_t offset)
约束：该接口中的dst不需要32B对齐，但数据类型为T的dst需要sizeof(T) Byte对齐。；调用本接口之前，需要调用asc_storeunalign_postupdate使用uint32_t作为存储偏移量的接口，且本接口与前序接口的非对齐寄存器要保持一致。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
