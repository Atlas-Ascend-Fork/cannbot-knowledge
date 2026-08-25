---
type: API
title: AscCreateMask
description: 根据pat_mode生成掩码寄存器，支持b8、b16、b32三种位宽模式，指定参与计算的元素位置
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_create_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscCreateMask

根据传入的pat_mode生成对应的掩码寄存器，支持b8、b16、b32三种位宽模式。pat_mode参数指定mask的模式，即指定哪些位置的元素参与计算。 位宽模式说明： 图1 asc_create_mask原理
函数原型：asc_create_mask_b8(pat_mode)
返回值：vector_bool，掩码寄存器。
约束：本接口仅在AIV上生效，非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；掩码寄存器的数量上限为8，超过上限的掩码寄存器会写入预留的8K UB内存中，可能引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若两者均可用，优先复用寄存器。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [B16 比较先升到 B32 锁定索引 lane](../../../../../runbooks/precision/b16_value_and_b32_index_masks_need_common_b32_compute.md)（`exemplifies`）：AscCreateMask 与《B16 比较先升到 B32 锁定索引 lane》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [Reg CreateMask 缺类型参数导致编译失败](../../../../../runbooks/compilation/reg_createmask_requires_explicit_type.md)（`exemplifies`）：AscCreateMask 与《Reg CreateMask 缺类型参数导致编译失败》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [UpdateMask 引用参数拒绝 const — 改用可修改左值](../../../../../runbooks/compilation/updatemask_requires_mutable_uint32_lvalue.md)（`exemplifies`）：AscCreateMask 与《UpdateMask 引用参数拒绝 const — 改用可修改左值》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [半精度索引错位—拆分双 int32 掩码](../../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`exemplifies`）：AscCreateMask 与《半精度索引错位—拆分双 int32 掩码》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：AscCreateMask 与《如何使用掩码操作API》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [asc_create_iter_reg (废弃)](asc_create_iter_reg_deprecated.md)（`related`）：当前迭代通常由显式 AddrReg/Mask 管理，CreateMask 补充有效 lane。
- [AscGetMaskSpr](asc_get_mask_spr.md)（`same_topic`）：AscCreateMask 与《AscGetMaskSpr》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [AscUpdateMask](asc_update_mask.md)（`same_topic`）：AscCreateMask 与《AscUpdateMask》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [MaskGenWithRegTensor](../../../basic_api/reg_vector_compute/reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`same_topic`）：AscCreateMask 与《MaskGenWithRegTensor》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [MaskMergeMode](../../../basic_api/reg_vector_compute/aux_data_types/mask_merge_mode.md)（`same_topic`）：AscCreateMask 与《MaskMergeMode》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [MaskReg](../../../basic_api/reg_vector_compute/register_data_types/mask_reg.md)（`same_topic`）：MaskReg 卡定义基础 API 掩码寄存器的创建与位模式，AscCreateMask 是 C API 创建同类掩码寄存器的入口；两者描述同一掩码对象的跨语言合同。
- [reg数据类型定义](data_type_definition.md)（`same_topic`）：AscCreateMask 与《reg数据类型定义》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [寄存器数据类型](reg_data_types.md)（`same_topic`）：AscCreateMask 与《寄存器数据类型》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
<!-- cannbot:related:end -->
