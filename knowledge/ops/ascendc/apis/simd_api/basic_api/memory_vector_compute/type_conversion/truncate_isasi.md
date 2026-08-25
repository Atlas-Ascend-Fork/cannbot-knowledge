---
type: API
title: Truncate
description: 将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Truncate_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Truncate

将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。

将源操作数的浮点数元素截断到整数位，同时源操作数的数据类型保持不变。

本接口属于 UB 矢量计算类型转换接口。

参数说明：T：操作数数据类型。；roundMode：舍入模式，取值如下。 **RoundMode::CAST_RINT**：返回最接近的整数，若存在两个同样接近的整数，则选择偶数。 **RoundMode::CAST_ROUND**：四舍五入取整。 **RoundMode::CAST_FLOOR**：向下取整。 **RoundMode::CAST_CEIL**：向上取整。 **RoundMode::CAST_TRUNC**：截断取整（直接舍弃小数部分）。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。 源操作数的数据类型需要与目的操作数保持一致。；count：输入 参与计算的元素个数。

约束：操作数地址对齐要求请参见通用地址对齐约束。；针对Ascend 950PR/Ascend 950DT，该接口通过VF调用Reg矢量计算API实现兼容，当参数count取值为0时，不保证该接口被视为NOP（空操作）。
