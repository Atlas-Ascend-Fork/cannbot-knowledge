---
type: API
title: Add
description: 对srcReg0和srcReg1按元素求和，结果写入dstReg，可选保留进位。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Add

对srcReg0和srcReg1按元素求和，结果写入dstReg，可选保留进位。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reg 尾块 masked Add 清零跨块累加器](../../../../../runbooks/precision/reg_tail_mask_zeroing_clears_cross_chunk_accumulator.md)（`exemplifies`）：故障发生在 masked Reg《Add》更新跨块 accReg；修复把该 Add 的 mask 从 tailMask 改为 fullMask，以 acc+0 保留历史 lane。
- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：Add 的第三数据参数是 RegTensor，符合 Reduce 产生的 lane0 寄存器结果，是本卡经构建验证的替换接口。
- [Add](../../memory_vector_compute/basic_arithmetic/add.md)（`related`）：Add 与《Add》的实质衔接是：Reg Add 与 C API Add 实现相同逐 lane 加法；complex32/64 是该接口支持复数重载时所需的操作数契约。
- [AddC](add_c.md)（`related`）：AddC 与《Add》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [Adds](adds.md)（`related`）：Add 的第二输入是 RegTensor；需要累加寄存器结果而非标量常量时必须由 Adds 切换到 Add。
- [complex32/complex64](../../aux_data_structures/complex32_complex64.md)（`related`）：Add 与《complex32/complex64》的实质衔接是：Reg Add 与 C API Add 实现相同逐 lane 加法；complex32/64 是该接口支持复数重载时所需的操作数契约。
- [SubC](sub_c.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；Add正文说明“对srcReg0和srcReg1按元素求和，结果写入dstReg，可选保留进位”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
<!-- cannbot:related:end -->
