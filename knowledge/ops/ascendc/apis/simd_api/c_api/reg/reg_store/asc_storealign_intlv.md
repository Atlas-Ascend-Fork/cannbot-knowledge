---
type: API
title: AscStorealignIntlv
description: 从两个矢量数据寄存器交错搬出元素到UB，将src0、src1的元素交错存储于dst中，存储长度为VL*2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_intlv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealignIntlv

从矢量数据寄存器交错搬出到UB的接口，忽略mask，将src0、src1中的元素交错存储于dst中，存储长度为VL*2。支持数据类型为b8、b16、b32。
函数原型：void asc_storealign_intlv(__ubuf__ int8_t* dst_align32b, vector_int8_t src0, vector_int8_t src1)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
