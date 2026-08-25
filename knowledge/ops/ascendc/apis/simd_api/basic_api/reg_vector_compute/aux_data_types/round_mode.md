---
type: API
title: RoundMode
description: 枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/RoundMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# RoundMode

枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

# RoundMode | 参数名 | 描述 | | :-- | :-- | | RoundMode | 用于设置控制舍入模式。 enum class RoundMode { CAST_NONE = 0, CAST_RINT, CAST_FLOOR, CAST_CEIL, CAST_ROUND, CAST_TRUNC, CAST_ODD, CAST_HYBRID }; • CAST_NONE：当转换过程存在精度损失时，按 CAST_RINT 模式处理；当不存在精度损失时，不进行舍入。 • CAST_RINT：向最近的偶数舍入。 - 若待舍入部分的首位为 0，则不进位。 - 若待舍入部分的首位为 1 且后续位不全为 0，则进位。 - 若待舍入部分的首位为 1 且后续位全为 0：当非舍入部分的末位为 0，则不进位。当非舍入部分的末位为 1，则进位。 • CAST_FLOOR：向负无穷大方向舍入。 - 若符号位（S）为 0（正数），不进位。 - 若符号位（S）为 1（负数）：当待舍入部分全为 0，则不进位。否则，进位。 • CAST_CEIL：向正无穷大方向舍入。 - 若符号位（S）为 1（

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：RoundMode 与《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
- [FP16 算子 Cast 提升-计算-回退链设计](../../../../../runbooks/precision/fp16_cast_up_fp32_compute_cast_down_chain.md)（`exemplifies`）：FP16 算子 Cast 提升-计算-回退链设计 与《RoundMode》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《RoundMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](../../../../../runbooks/precision/bf16_cast_cast_rint.md)（`exemplifies`）：RoundMode 接口枚举定义 CAST_NONE、CAST_RINT 等舍入语义，本卡说明扩精度无舍入与缩精度需舍入的调用边界。
- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../../../../../runbooks/compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`exemplifies`）：RoundMode 与《f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
- [Cast](../type_conversion/cast.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《RoundMode》说明枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [CastFloatToHalfInt32](../../scalar_compute/cast_float_to_half_int32.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《RoundMode》说明枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [Lroundf](../../../../simt_api/math_functions/float_math_functions/lroundf.md)（`related`）：Lroundf 与《RoundMode》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Truncate](../../memory_vector_compute/type_conversion/truncate_isasi.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《RoundMode》明确“枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncate](../type_conversion/truncate.md)（`related`）：RoundMode 定义 Truncate 的五种舍入行为，直接决定半整数与负数的结果。
- [舍入模式与饱和模式](../../../c_api/reg/data_type_convert/rounding_mode.md)（`related`）：RoundMode 与《舍入模式与饱和模式》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
- [SatMode](sat_mode.md)（`same_topic`）：RoundMode 与《SatMode》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
<!-- cannbot:related:end -->
