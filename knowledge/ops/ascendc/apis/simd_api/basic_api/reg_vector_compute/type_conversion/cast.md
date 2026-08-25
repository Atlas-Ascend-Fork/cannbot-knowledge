---
type: API
title: Cast
description: Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/type_conversion/Cast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Cast

Cast用于数据类型精度转换，将源操作数数据类型转换成目的操作数数据类型，能够实现浮点转整数、浮点转浮点、整数转浮点、整数转整数的数据类型转换。转换过程中，由于位宽变化、精度变化，支持配置如下参数进行功能实现
- RegLayout：源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。
- SatMode：用于设置饱和与不饱和模式。
- MaskMergeMode：用于指定写入寄存器数据模式，mask未选择的元素在dst中置零或保留dst原值。
- RoundMode：用于设置舍入模式。

不同数据类型下元素对应的mask位宽不一致，在Cast进行类型转换时，MaskReg根据输入的源操作数进行有效元素筛选。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h"。

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；U: 源操作数的数据类型。支持的数据类型请参考数据类型。；trait: CastTrait类型，类型转换模式结构体。包括RegLayout、SatMode、MaskMergeMode、RoundMode。 struct CastTrait { RegLayout layoutMode = RegLayout::UNKNOWN; SatMode satMode = SatMode::UNKNOWN; MaskMergeMode mrgMode = MaskMergeMode::UNKNOWN; RoundMode roundMode = RoundMode::UNKNOWN; }; 使能SatMode生效需与SetCtrlSpr配合使用。不饱和模式和饱和模式的具体配置请参考表5 饱和模式全局或单指令生效配置表。 注：SetCtrlSpr需在SIMD_VF外调用。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；V: 源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。 注：mask会按照输入来筛选。

约束：- 当目的操作数位宽比源操作数小时，再MaskReg和RegLayout作用下，目的操作数中的无效元素均为0。
- 该指令需配合SetCtrlSpr指令使用，通过设置寄存器的值控制Cast的不饱和模式和饱和模式。
- 舍入模式仅在可能导致精度损失且支持该舍入模式的转换中生效。
- 不同类型转换的不饱和与饱和模式的描述有所区别，全局或单指令生效配置方法也不同。
- 浮点数转浮点数
    - 当输出类型float32时，只支持不饱和模式。
    - 不饱和模式：当输出类型为fp8_e4m3fn_t时，由于fp8_e4m3fn_t没有inf表示格式，所以输出为nan。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](../../../../../runbooks/precision/b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Cast》说明在RegTensor间执行数值类型转换，并通过CastTrait配置舍入、饱和和mask行为。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》说明dav-3510 上高层 AscendC::Cast 与底层 Reg::Cast 对 b16↔fp32 一律硬编码 SatMode::SAT，fp16 NaN/Inf 在第一次 b16→fp32 Cast 即被饱和为 65504，castTrait 调参（NO_SAT/默认/参考 castTraitB16ToB32）与 PostElewise Compare+Select 均无法恢复 NaN/Inf，禁止作为 NaN/Inf 传播配方。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [CastTrait 按值 NTTP 在 C++17 编译失败](../../../../../runbooks/compilation/casttrait_nttp_uses_reference_in_cxx17.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《CastTrait 按值 NTTP 在 C++17 编译失败》说明AscendC Reg CastTrait 作为按值非类型模板参数需要 C++20；C++17 direct-launch 工程改用静态 constexpr 对象的 const 引用 NTTP。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [CastTrait 文件域声明触发命名空间编译失败](../../../../../runbooks/compilation/reg_casttrait_define_inside_simd_vf.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《CastTrait 文件域声明触发命名空间编译失败》说明CANN 9.0.1 的 dav-3510 Reg kernel 在文件域声明 CastTrait 会被 bisheng 拒绝；将常量移入 __simd_vf__ 函数域后编译链接通过。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](../../../../../runbooks/compilation/reg_cast_requires_explicit_zeroing_trait.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING》说明dav-3510 Reg::Cast 的默认 CastTrait 使用 MaskMergeMode::UNKNOWN，设备实现静态断言只接受 ZEROING 或 MERGING，需传显式 trait。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：该故障卡锁定的失真组合直接包含 Reg《Cast》：DIST_UNPACK_B16 后转换并写回 UB 时部分 lane 布局不再 1:1。
- [MaskMergeMode](../aux_data_types/mask_merge_mode.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《MaskMergeMode》说明枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [RegLayout](../aux_data_types/reg_layout.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《RegLayout》说明源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。更多特性说明请参考Cast。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [RoundMode](../aux_data_types/round_mode.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《RoundMode》说明枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [SatMode](../aux_data_types/sat_mode.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《SatMode》说明SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT, SAT };&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；&bull;&nbsp;&nbsp;SAT：饱和模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [Truncate](../../memory_vector_compute/type_conversion/truncate_isasi.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Cast》明确“Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncate](truncate.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Truncate》说明将源操作数中的浮点数元素截断为整数值并保留原数据类型，存入目的操作数。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [__float2int_rn](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rn.md)（`related`）：__float2int_rn 与《Cast》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rz](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rz.md)（`related`）：__float2int_rz 与《Cast》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [类型转换](type_conversion.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《类型转换》说明寄存器矢量类型转换接口集合，包含Cast和Truncate接口。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [Cast](../../memory_vector_compute/type_conversion/cast.md)（`same_topic`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Cast》说明根据源操作数和目的操作数的数据类型进行精度转换，支持多种舍入模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
<!-- cannbot:related:end -->
