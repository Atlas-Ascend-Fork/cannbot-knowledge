---
type: API
title: Silu接口
description: 提供Silu激活函数接口及GetSiluTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Silu_interface/Silu_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Silu接口

提供 Silu 激活函数及 GetSiluTmpSize 临时空间查询接口。Silu 按元素计算 x * sigmoid(x)，又称 Swish（β=1 的特例）。

接口为模板函数，支持 half、float 数据类型，`isReuseSource` 参数预留。通过 `dataSize` 指定实际计算元素个数。仅支持 ND 格式输入，不支持源操作数与目的操作数地址重叠。操作数支持的 TPosition 为 VECIN/VECCALC/VECOUT。
