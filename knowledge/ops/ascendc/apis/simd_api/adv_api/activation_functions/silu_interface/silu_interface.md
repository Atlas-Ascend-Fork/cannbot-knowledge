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

<!-- cannbot:related:start -->
## 相关

- [GetSiluTmpSize](get_silu_tmp_size.md)（`related`）：《GetSiluTmpSize》明确“用于获取Silu Tiling参数：Silu接口能完成计算所需最大临时空间大小和最小临时空间大小。”；它与《Silu接口》的“提供Silu激活函数接口及GetSiluTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Silu](silu.md)（`same_topic`）：《Silu》明确“按元素做Silu激活运算，支持half和float数据类型，不支持源操作数与目的操作数地址重叠。”；它与《Silu接口》的“提供Silu激活函数接口及GetSiluTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
