---
type: API
title: Adds
description: 对srcReg按元素与标量求和，结果写入dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Adds.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Adds

对srcReg按元素与标量求和，结果写入dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：Adds 的第三数据参数是 C++ 标量，正是误把 Reduce 结果 RegTensor 传入后触发 vadds 类型断言的接口契约。
- [Add](add.md)（`related`）：Add 的第二输入是 RegTensor；需要累加寄存器结果而非标量常量时必须由 Adds 切换到 Add。
- [Adds](../../memory_vector_compute/basic_arithmetic/adds.md)（`same_topic`）：Reg Adds 与 Memory Tensor Adds 完成相同逐元素标量加法，可按数据驻留在 RegTensor 或 LocalTensor 选择。
<!-- cannbot:related:end -->
