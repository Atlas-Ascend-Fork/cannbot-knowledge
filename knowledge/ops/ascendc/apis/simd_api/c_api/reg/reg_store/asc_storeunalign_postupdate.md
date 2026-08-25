---
type: API
title: AscStoreUnalignPostupdate
description: 从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreUnalignPostupdate

reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。
函数原型：void asc_storeunalign_postupdate(__ubuf__ uint16_t*& dst, vector_store_unalign& src0, vector_bool src1)
约束：该接口中的dst不需要32B对齐。；使用uint32_t作为存储偏移量时，本接口应与asc_storeunalign_post_postupdate接口配合使用。asc_storeunalign_post_postupdate接口用于处理该场景下非对齐搬出的尾块。；使用addr_reg作为存储偏移量时，本接口应与asc_storeunalign_post接口配合使用。asc_storeunalign_post接口用于处理该场景下非对齐搬出的尾块。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
