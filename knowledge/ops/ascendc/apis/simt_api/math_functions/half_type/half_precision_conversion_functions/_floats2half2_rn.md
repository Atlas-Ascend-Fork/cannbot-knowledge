---
type: API
title: __floats2half2_rn
description: 将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__floats2half2_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __floats2half2_rn

功能：将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。

函数原型：half2 __floats2half2_rn(const float x, const float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：将输入float类型数据遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分的结果。本接口受全局饱和寄存器影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rd](_float22half2_rd.md)（`related`）：__float22half2_rd 与《__floats2half2_rn》的实质衔接是：float2→half2 RD 与饱和、其他舍入、反向 half2→float2 和双 float 拼装入口共享双 lane 窄化契约。
- [__float22half2_rn_sat](_float22half2_rn_sat.md)（`related`）：__float22half2_rn_sat 与《__floats2half2_rn》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__floats2bfloat162_rn](../../bfloat16_type/bfloat16_precision_conversion_functions/_floats2bfloat162_rn.md)（`related`）：两个标量按 RINT 打包的结构相同，但目标低精度类型从 half2 变为 bfloat16x2。
- [__halves2half2](_halves2half2.md)（`related`）：《__floats2half2_rn》明确“将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。”；它与《__halves2half2》的“将输入的数据分别填充为half2前后两个分量，返回填充后的数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float22half2_rn](_float22half2_rn.md)（`same_topic`）：floats2half2_rn 接收两个标量 float，float22half2_rn 接收一个 float2；二者舍入和 half2 打包结果一致。
<!-- cannbot:related:end -->
