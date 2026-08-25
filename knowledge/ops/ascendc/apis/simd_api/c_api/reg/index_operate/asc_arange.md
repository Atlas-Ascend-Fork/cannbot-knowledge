---
type: API
title: AscArange
description: 以指定起始值生成递增或递减索引序列并保存到矢量数据寄存器，仅在AIV上生效。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/index_operate/asc_arange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscArange

以传入的value为起始值，生成递增/递减的索引，并将生成的索引保存在dst中，Vector Length (VL)表示矢量数据寄存器的位宽，VL_T表示该寄存器可存储的元素数量。算法逻辑表示
以int16_t数据类型，起始值value=10为例
递增索引为{10, 11, 12, 13, ... 135, 136, 137}，递减索引为{137, 136, 135, 134, ... 12, 11, 10}。

本接口仅在AIV上生效。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；value(输入): 源操作数（标量），dtype须与dst一致。作为递增序列的起点，序列第0个元素等于value，后续元素按1递增。取值范围为该dtype的可表示范围。；dst(输出): 目的操作数（矢量数据寄存器）。；value(输入): 源操作数（标量），dtype须与dst一致。作为递减序列的起点，序列第0个元素等于value + VL_T - 1，后续元素按1递减。取值范围为该dtyp。

支持数据类型：half。

约束：- 本接口在非AIV上调用直接返回。
- 整型dtype（int8_t、int16_t、int32_t）结果在超出该dtype可表示范围时回绕（wrap-around），不触发异常。例如int8_t取value=127时，序列前128个元素依次为127、−128、−127、…、-2；value=−128时，序列前128个元素依次为−128、−127、…、−1。

仅 Ascend 950PR/Ascend 950DT 支持。
