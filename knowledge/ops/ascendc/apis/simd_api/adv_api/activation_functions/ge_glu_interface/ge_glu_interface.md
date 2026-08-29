---
type: API
title: GeGLU接口
description: 提供GeGLU激活函数接口及其Tiling临时空间大小查询接口，包含GeGLU、GetGeGLUMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/GeGLU_interface/GeGLU_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GeGLU接口

提供GeGLU激活函数接口及其Tiling临时空间大小查询接口，包含GeGLU、GetGeGLUMaxMinTmpSize等。

GeGLU是采用GELU作为激活函数的GLU变体。其中GELU激活函数的计算公式如下： 上述公式中的erf为误差函数： 误差函数没有解析表达式，按照业界普遍使用的tanh近似表达式： 将GELU近似公式代入可得GeGLU表达式为： 其中a=-0.0713548162726, b=2.2363860002236e1，x1和x0代表srcTensor1和srcTensor0中的元素。

本接口组包含 GeGLU。

本接口属于高阶激活函数接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；当前仅支持ND格式的输入，不支持其他格式。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
