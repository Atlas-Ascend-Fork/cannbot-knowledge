---
type: API
title: AscPackToLow
description: 将源操作数元素按位压缩写入目的操作数低半部分，支持bool、b16、b32、b64等位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_pack_to_low.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscPackToLow

将源操作数中的元素选取偶数位bit(bool)、低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分。
当源操作数为vector_bool时，其按bit位进行压缩，每2bit将其中的低位bit存储至目的操作数的低半部分。

参数：dst(输出): 目的操作数（矢量数据寄存器/掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器/掩码寄存器）。

支持数据类型：uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。
