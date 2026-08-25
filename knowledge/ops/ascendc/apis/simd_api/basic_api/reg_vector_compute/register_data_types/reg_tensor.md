---
type: API
title: RegTensor
description: RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/RegTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# RegTensor

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

参数：T: 操作数数据类型，支持的数据类型(宽度)为b8、b16、b32、b64。 • b8：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t（fp4x2_e2m1_t、fp4x2_e1m2_t这两个b4类型在Vector侧的内存排布需要为两个一组，表现为b8类型；int4b_t也使用b8类型表达；bool数据类型只支持数据搬运）。 • b16：int16_t、uint16_t、half、bfloat16_t。 • b32：int32_t、uint32_t、float、complex32。 • b64：int64_t、uint64_t、complex64。；regTrait: 类型为RegTrait，支持配置为RegTraitNumOne或RegTraitNumTwo。 • RegTraitNumOne：该RegTensor类型中包含1个相应数据类型的矢量Reg，长度为VL。支持的数据类型为：b8、b16、b32、b64。 • RegTraitNumTwo：该RegTensor类型中包含2个相应数据类型的矢量Reg，每个矢量Reg长度为VL，总长度为2*VL。支持的数据类型为：complex32、b64。

约束：-   RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。
-   寄存器的生命周期限定于单个VF内部。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：RegTensor 与《Ascend950 Reg 扫描按 256B 锁定 lane》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [RegTensor 使用 c10 低精度类型导致 TypeGet 未定义](../../../../../runbooks/compilation/device_templates_use_native_types_not_torch_wrappers.md)（`exemplifies`）：RegTensor 与《RegTensor 使用 c10 低精度类型导致 TypeGet 未定义》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：RegTensor 与《RegTensor 累加须用 Add 而非 Adds》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽](../../../../../runbooks/precision/regtensor_cross_chunk_state_should_persist_in_ub_slot.md)（`exemplifies`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《RegTensor》说明RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [complex32/complex64](../../aux_data_structures/complex32_complex64.md)（`related`）：complex32/complex64 与《RegTensor》的实质衔接是：complex32/complex64 定义 Reg 复数操作数布局，RegTensor 承载该类型；复数基础概览补充实部虚部与支持边界。
- [AddrReg](addr_reg.md)（`same_topic`）：RegTensor 与《AddrReg》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [MaskReg](mask_reg.md)（`same_topic`）：MaskReg 与《RegTensor》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [UnalignRegForLoadAndUnalignRegForStore](unalign_reg_for_load_unalign_reg_for_store.md)（`same_topic`）：UnalignRegForLoadAndUnalignRegForStore 与《RegTensor》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [内置数据类型（数据结构）](../../data_structures/builtin_data_types.md)（`same_topic`）：RegTensor 与《内置数据类型（数据结构）》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [寄存器数据类型](register_data_types.md)（`same_topic`）：RegTensor 与《寄存器数据类型》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
<!-- cannbot:related:end -->
