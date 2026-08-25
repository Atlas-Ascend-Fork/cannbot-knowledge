---
type: API
title: AscPackToHigh
description: 将源操作数元素的低位写入目的操作数的高半部分，支持b16、b32、b64和bool类型压缩。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_pack_to_high.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscPackToHigh

将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的高半部分。
当源操作数为vector_bool时，其按bit位进行压缩，每2bit将其中的低位bit存储至目的操作数的高半部分。

参数：dst(输出): 目的操作数（矢量数据寄存器/掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器/掩码寄存器）。

支持数据类型：uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。
