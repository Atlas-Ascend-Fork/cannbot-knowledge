---
type: API
title: 寄存器数据类型
description: Reg矢量计算API操作的基础寄存器数据类型介绍如下：
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/register_data_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 寄存器数据类型

Reg矢量计算API操作的基础寄存器数据类型介绍如下：

-   **RegTensor**
矢量数据寄存器，Reg矢量计算基本存储单元，用于矢量计算。RegTensor的位宽是VL（VectorLength），长度为256B，可存储VL/sizeof(T)个数据（T表示数据类型）。b64或complex32类型下，支持扩展存储2VL用于复杂计算。

-   **MaskReg**
掩码寄存器，用于矢量计算中选择参与计算的元素。MaskReg的位宽是VL/8，长度为32B。

-   **UnalignRegForLoad & UnalignRegForStore**
非对齐寄存器，作为缓冲区，用来优化UB和RegTensor之间的连续非对齐地址访问的开销。

-   **AddrReg**
地址寄存器，用于存储地址偏移量的寄存器。AddrReg通过调用CreateAddrReg接口根据每层循环所设置的stride进行地址偏移自增。
