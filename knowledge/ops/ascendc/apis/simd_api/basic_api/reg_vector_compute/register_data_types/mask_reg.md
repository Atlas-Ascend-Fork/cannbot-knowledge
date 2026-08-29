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
