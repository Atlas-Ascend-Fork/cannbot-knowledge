---
type: API
title: AscStorealignPackPostupdate
description: 从矢量或掩码寄存器压缩搬出到UB，根据mask将有效元素低半部分bit数据连续存储于dst，调用后自动更新目的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_pack_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealignPackPostupdate

从矢量数据寄存器或掩码寄存器压缩搬出到UB的接口，根据mask将src中有效元素的低半部分bit数据连续存储于dst中，接口调用后自动更新目的操作数地址。支持数据类型为b16、b32、b64。
函数原型：void asc_storealign_pack_postupdate(__ubuf__ int16_t*& dst_align32b, vector_int16_t src, int32_t offset, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
