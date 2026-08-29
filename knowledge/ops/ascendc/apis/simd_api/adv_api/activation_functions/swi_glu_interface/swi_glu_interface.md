---
type: API
title: SwiGLU接口
description: 提供SwiGLU激活函数接口及GetSwiGLUMaxMinTmpSize、GetSwiGLUTmpBufferFactorSize等Tiling查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SwiGLU_interface/SwiGLU_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SwiGLU接口

提供SwiGLU激活函数接口及GetSwiGLUMaxMinTmpSize、GetSwiGLUTmpBufferFactorSize等Tiling查询接口。

SwiGLU是采用Swish作为激活函数的GLU变体。其中Swish激活函数的计算公式如下（β为常量）：

本接口组包含 SwiGLU。

本接口属于高阶激活函数接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；当前仅支持ND格式的输入，不支持其他格式。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
