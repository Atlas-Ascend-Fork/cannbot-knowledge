---
type: API
title: 数据压缩
description: Reg矢量计算数据压缩接口索引页，包含Unsqueeze、Pack与UnPack。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/data_compression.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据压缩

提供 Unsqueeze、Pack 和 UnPack 寄存器级数据压缩解压接口。Unsqueeze 根据 mask 对 dstReg 解压缩，首位元素置 0，后续元素根据 mask 中 1 的累计数量递增。Pack 将 srcReg 元素的低位写入 dstReg 的低半或高半部分，支持 b16/b32/b64 类型。

这些接口均为寄存器级操作，仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
