---
type: API
title: __float22hif82_rna_sat
description: 饱和模式下，将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__float22hif82_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22hif82_rna_sat

功能：饱和模式下，将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __float22hif82_rna_sat(const float2 x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入的两个分量遵循CAST_ROUND模式转换成的hifloat8x2_t类型数据。特殊值：±0→0；nan→0；inf→32768；-inf→-32768；(超出hif8范围的正值,inf)→32768；(超出hif8范围的负值,-inf)→-32768。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [HiFloat8 SatMode::SAT Cast NaN 映射 0x00](../../../../../runbooks/precision/hifloat8_satmode_sat_cast_nan_0x00.md)（`exemplifies`）：精度卡的 device 路径正是 float→HiFloat8 SAT 转换；目标 API 给出同方向 RNA 饱和入口，可用于构造 NaN 字节级复现。
- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__float22hif82_rna_sat》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [__half22hif82_rna_sat](_half22hif82_rna_sat.md)（`related`）：《__float22hif82_rna_sat》明确“饱和模式下，将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”；它与《__half22hif82_rna_sat》的“饱和模式下，将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float22hif82_rh_sat](_float22hif82_rh_sat.md)（`same_topic`）：RNA 改变 tie 舍入规则。
- [__float22hif82_rna](_float22hif82_rna.md)（`same_topic`）：两接口都按 RNA 将 float2 转为 hifloat8x2，sat 版本仅改变饱和及特殊值映射，可逐字节对照转换结果。
<!-- cannbot:related:end -->
