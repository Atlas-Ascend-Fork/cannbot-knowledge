---
type: API
title: 舍入模式与饱和模式
description: 在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/rounding_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 舍入模式与饱和模式

在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。

在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。

- 舍入模式：主要用于浮点数之间的转换或浮点数转整数时，确定如何将高精度数值舍入到低精度表示。
- 饱和模式/非饱和模式：处理数值超出目标数据类型表示范围时的溢出行为。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int16](asc_float2int16.md)（`related`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《舍入模式与饱和模式》明确提供“在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [AscFloat2Int64](asc_float2int64.md)（`related`）：AscFloat2Int64 的结果由 RINT/ROUND/FLOOR/CEIL/TRUNC 和饱和模式共同决定；模式说明是解释溢出与小数取整行为的必要契约。
- [AscFloor](asc_floor.md)（`related`）：AscFloor说明将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。
- [AscHalf2Hif8](asc_half2hif8.md)（`related`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《舍入模式与饱和模式》明确“在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [AscHalf2Int16](asc_half2int16.md)（`related`）：舍入与饱和说明解释 AscHalf2Int16 的 RINT/ROUND/FLOOR/CEIL/TRUNC 及超范围处理，直接决定边界输入结果。
- [AscHalf2Int32](asc_half2int32.md)（`related`）：AscHalf2Int32 的五种后缀由舍入模式定义；该卡给出 RINT、ROUND、FLOOR、CEIL、TRUNC 与饱和行为的选择依据。
- [AscHalf2Uint8](asc_half2uint8.md)（`related`）：接口后缀的 RINT/ROUND/FLOOR/CEIL/TRUNC 以及 SAT/NO_SAT 语义由该卡定义，直接决定边界值结果。
- [AscRound](asc_round.md)（`related`）：AscRound说明将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。
- [RoundMode](../../../basic_api/reg_vector_compute/aux_data_types/round_mode.md)（`related`）：RoundMode 与《舍入模式与饱和模式》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
- [Round接口](../../../adv_api/math_compute/round_interface/round_interface.md)（`related`）：Round接口说明按元素四舍五入到最接近的整数，并提供临时空间大小获取接口。
- [asc_bfloat162e1m2x2 (废弃)](asc_bfloat162e1m2x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《舍入模式与饱和模式》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_float2e5m2 (废弃)](asc_float2e5m2_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《舍入模式与饱和模式》具体提供“在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [asc_half2int4x2 (废弃)](asc_half2int4x2_deprecated.md)（`same_topic`）：asc_half2int4x2 (废弃) 与《舍入模式与饱和模式》的实质衔接是：废弃 half→int4x2 转换需对照 int4 逆转换、当前 half 整数转换和舍入/饱和语义迁移。
<!-- cannbot:related:end -->
