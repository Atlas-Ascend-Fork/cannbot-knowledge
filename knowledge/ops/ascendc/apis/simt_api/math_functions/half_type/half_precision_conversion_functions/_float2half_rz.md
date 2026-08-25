---
type: API
title: __float2half_rz
description: 遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_rz

功能：遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值。

函数原型：half __float2half_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的半精度浮点数。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2half](_float2half.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；__float2half_rz正文界定“遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rd](_float2half_rd.md)（`same_topic`）：__float2half_rd说明遵循CAST_FLOOR模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rd_sat](_float2half_rd_sat.md)（`same_topic`）：__float2half_rd_sat说明将浮点数转换为half类型数据，并遵循CAST_FLOOR模式，返回转换后的值。
- [__float2half_rn](_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；__float2half_rz正文说明“遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
- [__float2half_rn_sat](_float2half_rn_sat.md)（`same_topic`）：__float2half_rn_sat说明饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值。
- [__float2half_rna](_float2half_rna.md)（`same_topic`）：__float2half_rna说明遵循CAST_ROUND模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_rna_sat](_float2half_rna_sat.md)（`same_topic`）：__float2half_rna_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值。
- [__float2half_ro](_float2half_ro.md)（`same_topic`）：__float2half_ro说明遵循CAST_ODD模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_ro_sat](_float2half_ro_sat.md)（`same_topic`）：__float2half_ro_sat说明将浮点数转换为半精度浮点数，并遵循CAST_ODD模式，返回转换后的值。
- [__float2half_ru](_float2half_ru.md)（`same_topic`）：__float2half_ru：所选接口保持 float→half 类型对不变，只切换 RU 的饱和版或 RD/RN/RNA/RO/RZ舍入，可直接比较特殊值和边界输出。 目标卡《__float2half_rz》补充：遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值。
- [__float2half_ru_sat](_float2half_ru_sat.md)（`same_topic`）：__float2half_ru_sat说明将浮点数转换为半精度浮点数，并遵循CAST_CEIL模式，返回转换后的值。
- [__float2half_rz_sat](_float2half_rz_sat.md)（`same_topic`）：__float2half_rz_sat：__float2half_rz_sat与非饱和RZ及half2向量版共享转换契约；其他sat卡只改变舍入方向，可直接核对CTRL饱和位、Inf/NaN和边界值。 目标卡《__float2half_rz》补充：遵循CAST_TRUNC模式，将浮点数转换为半精度浮点数，返回转换后的值。
<!-- cannbot:related:end -->
