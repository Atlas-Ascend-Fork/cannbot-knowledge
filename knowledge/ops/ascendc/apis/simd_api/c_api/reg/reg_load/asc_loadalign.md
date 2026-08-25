---
type: API
title: AscLoadalign
description: 从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalign

将Unified Buffer（UB）中起始地址32字节对齐的数据搬入矢量数据寄存器或掩码寄存器，搬运过程中数据格式和内容保持不变。本接口提供四种功能模式： 本接口仅在AIV上生效，非AIV调用直接返回。
约束：本接口仅在AIV上生效，非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；实际读取的UB地址和偏移后的UB地址必须32字节对齐，并且在UB地址空间内且不越界，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
