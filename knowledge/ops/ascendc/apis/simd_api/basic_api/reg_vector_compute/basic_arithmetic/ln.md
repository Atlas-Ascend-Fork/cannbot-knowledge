---
type: API
title: Ln
description: 根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Ln.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Ln

根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Log2](log2.md)（`related`）：《Log2》说明根据mask对源操作数逐元素求以2为底的对数，将结果写入目的操作数。；《Ln》说明根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。。二者在Reg Log2与Ln、Log/Log10共享对数语义但底数不同，选择时必须区分结果定义上存在可执行的直接衔接。
- [Log](log.md)（`same_topic`）：Ln 与《Log》的实质衔接是：Ln 与 Log 都在 RegTensor 上按 mask 求自然对数；Log 采用标准库命名，是正文明确的等价入口，而 Log10/Log2 底数不同。
<!-- cannbot:related:end -->
