---
type: API
title: AscIntlv
description: 将源操作数src0和src1中的元素交织存入目的操作数dst0和dst1中，支持掩码寄存器和矢量数据寄存器两种操作数类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_rearrange/asc_intlv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscIntlv

将源操作数src0和src1中的元素交织存入目的操作数dst0和dst1中。按照操作数类型划分，可以分以下场景
操作数为掩码寄存器
- 不同数据类型的接口决定了交织的位宽大小，例如对于b32类型，交织时以4bit为一组，对于b16类型，交织时以2bit为一组。

操作数为矢量数据寄存器
- 以元素为单位进行交织。以int8_t矢量数据寄存器为例，交织过程如下图所示。

参数：dst0(输出): 目的操作数（矢量数据寄存器或掩码寄存器）。；dst1(输出): 目的操作数（矢量数据寄存器或掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器或掩码寄存器）。；src1(输入): 源操作数（矢量数据寄存器或掩码寄存器）。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、hifloat8_t、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- src0、src1、dst0、dst1的数据类型需要保持一致。
- src0和src1可以为同一个矢量数据寄存器或掩码寄存器。
- dst0和dst1不能为同一个矢量数据寄存器或掩码寄存器。
- 允许源操作数和目的操作数为同一个矢量数据寄存器或掩码寄存器，例如asc_intlv(src0, src1, src0, src1)。

仅 Ascend 950PR/Ascend 950DT 支持。
