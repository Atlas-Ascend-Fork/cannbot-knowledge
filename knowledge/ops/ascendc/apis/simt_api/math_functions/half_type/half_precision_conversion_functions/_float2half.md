---
type: API
title: __float2half
description: 遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half

功能：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。

函数原型：half __float2half(const float x)

参数：x（输入）源操作数。

返回值：将float类型数据按照CAST_RINT模式转换为half类型数据。特殊值：±0→±0；nan→±0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2half_ro_sat](_float2half_ro_sat.md)（`related`）：__float2half说明遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [AscFloat2Half](../../../../simd_api/c_api/reg/data_type_convert/asc_float2half.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；AscFloat2Half正文界定“将float类型数据转换成half类型，并支持多种舍入模式与饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [AscFloat2half](../../../../simd_api/c_api/vector_compute/asc_float2half.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；AscFloat2half正文界定“将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rd](_float2half_rd.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_rd正文界定“遵循CAST_FLOOR模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half正文说明“遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rna](_float2half_rna.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_rna正文界定“遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_ro](_float2half_ro.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_ro正文界定“遵循CAST_ODD模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_ru](_float2half_ru.md)（`same_topic`）：__float2half_ru：所选接口保持 float→half 类型对不变，只切换 RU 的饱和版或 RD/RN/RNA/RO/RZ舍入，可直接比较特殊值和边界输出。 目标卡《__float2half》补充：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rz](_float2half_rz.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_rz正文界定“遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rz_sat](_float2half_rz_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half》补充：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
<!-- cannbot:related:end -->
