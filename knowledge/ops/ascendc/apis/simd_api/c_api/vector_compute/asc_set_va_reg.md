---
type: API
title: AscSetVaReg
description: 用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_va_reg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetVaReg

用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。
函数原型：void asc_set_va_reg(ub_addr8_t addr, __ubuf__ int8_t** src_array)
参数：addr（输入）：地址寄存器，类型为ub_addr8_t，可取值为： &bull; VA0 &bull; VA1 &bull; VA2 &bull; VA3 &bull; VA4 &bull; VA5 &bull; VA6 &bull; VA7 数字代表寄存器顺序，每个地址寄存器只能关联8个地址，使用方法请参考调用示例；src_array（输入）：操作数地址序列。
约束：操作数地址对齐约束请参考存储单元说明。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscTranspose](asc_transpose.md)（`related`）：“AscSetVaReg”定义：用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。；“AscTranspose”定义：用于实现16*16的二维矩阵数据块转置。。实质衔接：AscSetVaReg 先把 16 个 DataBlock 地址写入 VA 寄存器，随后 C/基础 Transpose 消费这些地址完成 16×16 转置。
- [Transpose](../../basic_api/memory_vector_compute/data_layout_conversion/transpose.md)（`related`）：“AscSetVaReg”定义：用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。；“Transpose”定义：实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。。实质衔接：AscSetVaReg 先把 16 个 DataBlock 地址写入 VA 寄存器，随后 C/基础 Transpose 消费这些地址完成 16×16 转置。
<!-- cannbot:related:end -->
