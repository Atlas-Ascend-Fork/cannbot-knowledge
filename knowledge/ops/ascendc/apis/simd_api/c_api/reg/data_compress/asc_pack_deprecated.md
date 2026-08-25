---
type: API
title: asc_pack (废弃)
description: 该接口已废弃，请使用 asc_pack_to_low 和 asc_pack_to_high 替代。 将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分或高半部分。
  - asc_pack：将源操作数写入目的操作数的低半部分。 - asc_pack_v2：将源操作数写入目的操作数的高半部分。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_pack_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_pack (废弃)

该接口已废弃，请使用 asc_pack_to_low 和 asc_pack_to_high 替代。

将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分或高半部分。

- asc_pack：将源操作数写入目的操作数的低半部分。

- asc_pack_v2：将源操作数写入目的操作数的高半部分。

参数：dst(输出): 目的操作数（矢量数据寄存器/掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器/掩码寄存器）。

支持数据类型：int16_t、int32_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。
