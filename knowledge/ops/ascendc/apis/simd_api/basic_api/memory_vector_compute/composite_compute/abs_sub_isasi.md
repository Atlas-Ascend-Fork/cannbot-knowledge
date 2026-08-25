---
type: API
title: AbsSub
description: 将src0与src1相减再求绝对值，并将计算结果写入dst。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/AbsSub_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AbsSub

将src0与src1相减再求绝对值，并将计算结果写入dst。

将src0与src1相减再求绝对值，并将计算结果写入dst。计算公式如下：

本接口属于 UB 矢量计算接口。

参数说明：T：操作数数据类型。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；src0、src1：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。 两个源操作数的数据类型需要与目的操作数保持一致。；count：输入 参与计算的元素个数。

约束：操作数地址对齐要求请参见通用地址对齐约束。；操作数地址重叠约束请参考通用地址重叠约束。；该接口通过VF调用Reg矢量计算API实现兼容，当参数count取值为0时，不保证该接口将被视为NOP（空操作）。

<!-- cannbot:related:start -->
## 相关

- [AbsSub](../../reg_vector_compute/composite_compute/abs_sub.md)（`related`）：两者都执行逐元素 abs(src0-src1)，但 focal 从 LocalTensor 直接计算，Reg 版本以 RegTensor+mask 工作；可按内存/寄存器编程模型迁移。
- [AscAbsSub](../../../c_api/reg/compound_compute/asc_abs_sub.md)（`related`）：asc_abs_sub 提供同一减后取绝对值的 C Reg 接口及 mask 语义，是从 C++ Memory AbsSub 下沉到 C API Reg 编程的直接对应。
<!-- cannbot:related:end -->
