---
type: API
title: AscUnpack
description: 将源操作数低半或高半部分元素扩充位宽后写入目的操作数，支持无符号、有符号及bool类型
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_unpack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUnpack

将src中低半部分或高半部分的元素以扩充位宽的方式写入dst，支持
- asc_unpack_lower：取src的低半部分（LOWER），每个元素高位填0扩充位宽后写入dst。
- asc_unpack_upper：取src的高半部分（HIGHER），每个元素高位填0扩充位宽后写入dst。

不同数据类型的扩充方式
- 无符号整型：高位填0扩充。例如vector_uint8_t到vector_uint16_t，src中每个uint8_t元素高位补0扩展为uint16_t。
- 有符号整型：保持符号位扩充。例如vector_int8_t到vector_int16_t，src中每个int8_t元素按符号位扩展为int16_t。
- bool类型（掩码寄存器）：将每bit展开为2bit，高位填0。

矢量数据寄存器unpack流程如图1所示
掩码数据寄存器unpack流程如图2所示

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（掩码寄存器）。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscPackToLow](asc_pack_to_low.md)（`related`）：将源操作数中的元素选取偶数位bit(bool)、低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分。；将src中低半部分或高半部分的元素以扩充位宽的方式写入dst，支持。AscPackToLow 抽取低位并压入目的低半，AscUnpack 从低半或高半取出并扩宽，二者是寄存器宽度压缩与恢复的配套操作。
<!-- cannbot:related:end -->
