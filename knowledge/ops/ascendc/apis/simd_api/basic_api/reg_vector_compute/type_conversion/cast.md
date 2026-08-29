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

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：焦点卡说明“使能SatMode生效需与SetCtrlSpr配合使用。”，候选卡却在 dav-3510 实测“在 dav-3510 上经 Cast 传播 NaN/Inf 的路线 banned”；该 runbook 给出 SAT 硬编码导致 fp16 NaN/Inf 变为 65504 的失效边界和 bypass 方向。
- [CastTrait 文件域声明触发命名空间编译失败](../../../../../runbooks/compilation/reg_casttrait_define_inside_simd_vf.md)（`exemplifies`）：焦点卡要求 Cast 通过“trait: CastTrait类型，类型转换模式结构体。包括RegLayout、SatMode、MaskMergeMode、RoundMode。”配置，候选卡给出“把完整 trait 定义放到消费它们的 `__simd_vf__` 函数体内”的已验证声明位置；它解决同一 `.asc` Host/Device 分域下 CastTrait 不可见的构建故障。
- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](../../../../../runbooks/compilation/reg_cast_requires_explicit_zeroing_trait.md)（`exemplifies`）：CANN 9.0.1 的默认 `castTrait` 将 `MaskMergeMode` 置为 `UNKNOWN`，而 dav-3510 的 `Reg::Cast` 实现静态约束只接受 `ZEROING` 或 `MERGING`。；trait: CastTrait类型，类型转换模式结构体。包括RegLayout、SatMode、MaskMergeMode、RoundMode。 struct CastTrait { RegLayout layoutMode = RegLayout::UNKNOWN; SatMode satMode = SatMode::UNKNOWN; MaskMergeMode mrgMode = MaskMergeMode::UNKNOWN; RoundMode roundMode = RoundMode::UNKNOWN; };。Runbook 复现默认 UNKNOWN merge mode 在 dav-3510 被静态断言拒绝并要求显式 ZEROING/MERGING，API 卡给出 CastTrait 的默认字段，形成接口默认值到编译失败再到显式 trait 修复的验证链。
- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：焦点卡把 RoundMode 列入“trait: CastTrait类型，类型转换模式结构体。包括RegLayout、SatMode、MaskMergeMode、RoundMode。”，候选卡定位“`RoundMode` 的声明位于外层 `AscendC`”；该 runbook 给出 CastTrait 字段正确限定名及编译验证路径。
- [RegLayout](../aux_data_types/reg_layout.md)（`related`）：源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。更多特性说明请参考Cast。；RegLayout：源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。。候选 Cast 通过 CastTrait 实际消费焦点枚举来控制窄位元素布局。
<!-- cannbot:related:end -->
