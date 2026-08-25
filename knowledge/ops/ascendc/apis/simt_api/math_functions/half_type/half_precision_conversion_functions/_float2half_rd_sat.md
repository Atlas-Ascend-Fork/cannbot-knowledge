---
type: API
title: __float2half_rd_sat
description: 将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_rd_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_rd_sat

功能：将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。

函数原型：half __float2half_rd_sat(const float x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_FLOOR模式转换成的half类型数据。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2half](../../../../simd_api/c_api/vector_compute/asc_float2half.md)（`related`）：AscFloat2half说明将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float22half2_rd_sat](_float22half2_rd_sat.md)（`related`）：《__float22half2_rd_sat》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float2half_rd_sat》说明将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。。二者在float2到half2的向下舍入与饱和是两个独立维度，同输入输出的非饱和版和其他舍入版可直接对照上存在可执行的直接衔接。
- [__float2half_rd](_float2half_rd.md)（`same_topic`）：__float2half_rd说明遵循CAST_FLOOR模式，将浮点数转换为半精度浮点数，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_rd_sat正文说明“将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rn_sat](_float2half_rn_sat.md)（`same_topic`）：__float2half_rn_sat说明饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rna_sat](_float2half_rna_sat.md)（`same_topic`）：__float2half_rna_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_ro_sat](_float2half_ro_sat.md)（`same_topic`）：__float2half_ro_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_ru_sat](_float2half_ru_sat.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：__float2half_rd_sat说明将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。
- [__float2half_rz_sat](_float2half_rz_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rd_sat》补充：将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。
<!-- cannbot:related:end -->
