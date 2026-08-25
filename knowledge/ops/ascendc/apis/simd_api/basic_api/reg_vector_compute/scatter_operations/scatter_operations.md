---
type: API
title: Reg矢量计算离散操作
description: 寄存器矢量离散操作接口集合，包含Gather接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/scatter_operations/scatter_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算离散操作

提供 Gather 接口，根据索引值 indexReg 将源操作数 srcReg 按元素收集到目的操作数 dstReg 中。indexReg 数据类型位宽需与目的操作数一致，索引值可重复。

当索引值超出 RegTensor 最大元素个数（VL/sizeof(T)）时，按取模方式更新索引。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。

<!-- cannbot:related:start -->
## 相关

- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：AscGather 与《Reg矢量计算离散操作》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather](gather.md)（`related`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Reg矢量计算离散操作》说明寄存器矢量离散操作接口集合，包含Gather接口。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
<!-- cannbot:related:end -->
