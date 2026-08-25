---
type: API
title: CastDequant
description: 对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/CastDequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CastDequant

对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。

本接口用于设置DEQSCALE寄存器的值，DEQSCALE寄存器位宽为64bit，用于Vector计算单元上的量化计算，寄存器中存放的参数在不同场景下的含义不同：

本接口组包含 SetDeqScale, SetVectorMask, LocalTensor, 掩码操作, 高维切分。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

支持的数据类型为 uint64_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：offset量化参数，int16_t类型，只有前9位有效。；vdeq地址对齐约束参考地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
