---
type: API
title: __int2half_rz_sat
description: 遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_rz_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2half_rz_sat

功能：遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __int2half_rz_sat(const int x)

参数：x（输入）源操作数。

返回值：遵循CAST_TRUNC模式，将输入int32数据转换成的half数据。特殊值：0→0；2049→2050；-2049→-2048；2147483647（int32_t最大值）→ASCRT_MAX_NORMAL_FP16；-2147483648（int32_t最小值）→-ASCRT_MAX_NORMAL_FP16。

约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2half_rn](_int2half_rn.md)（`same_topic`）：《__int2half_rn》的任务是“遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。”。《__int2half_rz_sat》具体提供“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”，它直接用于int32→half 的舍入与饱和组合选择。
- [__int2half_rna_sat](_int2half_rna_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rz_sat》明确提供“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rz](_int2half_rz.md)（`same_topic`）：《__int2half_rz》处理“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”。《__int2half_rz_sat》提供“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其具体合同或探针直接接入int32 到 half 的 TRUNC 与其他舍入/饱和组合选择。
<!-- cannbot:related:end -->
