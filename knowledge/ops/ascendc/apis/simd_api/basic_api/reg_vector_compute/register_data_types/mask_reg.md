---
type: API
title: MaskReg
description: MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之一。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# MaskReg

头文件引用路径为"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为的八分之一（VL/8）。如下图所示，当操作数类型为b8时，每一个element对应1bit MaskReg；当操作数类型为b16时，每一个element对应2bit MaskReg，且仅2bit中的最低位是有效的；当操作数类型为b32时，每一个element对应4bit MaskReg，且仅4bit中的最低位是有效的。

参数：T(输入): 模板参数，支持的数据类型为b8/b16/b32/b64。；mode(输入): 创建MaskReg的模式，enum class类型。 enum class MaskPattern { ALL, // 所有元素设置为有效数据 VL1, // 最低1个元素设置为有效数据 VL2, // 最低2个元素设置为有效数据 VL3, // 最低3个元素设置为有效数据 VL4, // 最低4个元素设置为有效数据 VL8, // 最低8个元素设置为有效数据 VL16, // 最低16个元素设置为有效数据 VL32, // 最低32个元素设置为有效数据 VL64, // 最低64个元素设置为有效数据 VL128, // 最低128个元素设置为有效数据 M3, // 3的倍数设置为有效数据 M4, // 4的倍数设置为有效数据 H, // 最低一半元素设置为有效数据 Q, // 最低四分之一元素设置为有效数据 ALLF = 15 // 所有元素设置为无效数据 };；regTrait(输入): 该参数默认值为RegTraitNumOne。；T(输入): 模板参数，支持的数据类型为b8、b16、b32、b64。；regTrait(输入): 该参数默认值为RegTraitNumOne。；scalarValue(输入/输出): 矢量计算需要操作的元素的具体数量，生成对应的MaskReg，元素有效范围从0到VL_T（一个位宽为VL的向量寄存器中能够存放VL_T个数据类型为T的元素）。 执行完该函数后，scalarValue会减去VL_T。 scalarValue = (scalarValue < VL_T) ? 0 : (scalarValue - VL_T)

约束：- MaskReg寄存器数量上限为8。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reg CreateMask 缺类型参数导致编译失败](../../../../../runbooks/compilation/reg_createmask_requires_explicit_type.md)（`exemplifies`）：MaskReg 与《Reg CreateMask 缺类型参数导致编译失败》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [UpdateMask 引用参数拒绝 const — 改用可修改左值](../../../../../runbooks/compilation/updatemask_requires_mutable_uint32_lvalue.md)（`exemplifies`）：MaskReg 与《UpdateMask 引用参数拒绝 const — 改用可修改左值》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [基于全局掩码复用的计算性能优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：MaskReg 与《基于全局掩码复用的计算性能优化》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [AscUpdateMask](../../../c_api/reg/reg_data_types/asc_update_mask.md)（`related`）：MaskReg 与《AscUpdateMask》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [MaskGenWithRegTensor](../reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`related`）：MaskGenWithRegTensor 的输出就是 MaskReg；MaskReg 位宽为 RegTensor 八分之一，解释 b16/b32 bit 广播后的固定 32B 结果。
- [MaskMergeMode](../aux_data_types/mask_merge_mode.md)（`related`）：MaskReg 与《MaskMergeMode》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [Pack](../mask_reg_compute/pack.md)（`related`）：《MaskReg》给出“MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之一。”；该约束/探针可直接复现、解释或前置验证《Pack》中的“根据低位或高位模式，将源操作数src的偶数位bit提取到dst的低半部分或高半部分。”。
- [Select](../mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《MaskReg》具体提供“MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之一。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [StoreAlignMaskReg](../reg_data_store/store_align_mask_reg.md)（`related`）：StoreAlignMaskReg 与《MaskReg》的实质衔接是：MaskReg Store 的对齐/非对齐形态依赖 MaskReg 生成，LoadAlign 是反向搬入，C API StoreAlign 提供同语义入口。
- [AscCreateMask](../../../c_api/reg/reg_data_types/asc_create_mask.md)（`same_topic`）：MaskReg 卡定义基础 API 掩码寄存器的创建与位模式，AscCreateMask 是 C API 创建同类掩码寄存器的入口；两者描述同一掩码对象的跨语言合同。
- [LoadAlign](../reg_data_load/load_align_mask_reg.md)（`same_topic`）：MaskReg 与《LoadAlign》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [MaskReg计算](../mask_reg_compute/mask_reg_compute.md)（`same_topic`）：MaskReg 与《MaskReg计算》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [RegTensor](reg_tensor.md)（`same_topic`）：MaskReg 与《RegTensor》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [StoreUnAlignMaskReg](../reg_data_store/store_un_align_mask_reg.md)（`same_topic`）：MaskReg 与《StoreUnAlignMaskReg》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [UnalignRegForLoadAndUnalignRegForStore](unalign_reg_for_load_unalign_reg_for_store.md)（`same_topic`）：UnalignRegForLoadAndUnalignRegForStore 与《MaskReg》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [寄存器数据类型](register_data_types.md)（`same_topic`）：MaskReg 与《寄存器数据类型》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
<!-- cannbot:related:end -->
