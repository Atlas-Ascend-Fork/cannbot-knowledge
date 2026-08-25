---
type: API
title: __asc_cvt_float2_to_fp8x2
description: 将float2的两个分量按CAST_RINT模式转换为FP8类型（e4m3或e5m2）的8位浮点数，支持饱和与非饱和溢出处理，结果以位级打包存储。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__asc_cvt_float2_to_fp8x2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __asc_cvt_float2_to_fp8x2

功能：将float2类型数据的两个分量，按照CAST_RINT模式转换为指定类型（float8_e4m3x2_t和float8_e5m2x2_t）的8位浮点数，并根据指定的饱和模式（饱和或非饱和）进行溢出处理。转换结果以位级打包形式存储为__asc_fp8x2_storage_t类型，该类型为16位无符号整数unsigned short int，用于存储float8_e4m3x2_t或float8_e5m2x2_t类型的数据。

函数原型：__asc_fp8x2_storage_t __asc_cvt_float2_to_fp8x2(const float2 x, const __asc_saturation_t saturate, const __asc_fp8_interpretation_t fp8_interpretation)

参数：x（输入）源操作数，saturate（输入）控制饱和行为，支持的取值为：__ASC_NOSAT、__ASC_SATFINITE。<br><br>__ASC_NOSAT表示使用非饱和模式，__ASC_SATFINITE表示使用饱和模式，fp8_interpretation（输入）指定转换类型，支持的取值为：__ASC_E4M3、__ASC_E5M2。<br><br>__ASC_E4M3表示转换为float8_e4m3x2_t格式的浮点数，__ASC_E5M2表示转换为float8_e5m2x2_t格式的浮点数。

返回值：输入的两个分量遵循CAST_RINT模式，根据指定的8位浮点数类型和指定的饱和模式，转换成的__asc_fp8x2_storage_t类型数据。本接口受全局饱和模式影响，。特殊值：(各分量输入,非饱和模式返回值)→饱和模式返回值；±0→±0；nan→+0；±inf→±448；(超出float8_e4m3_t范围的正值,nan)→448；(超出float8_e4m3_t范围的负值,nan)→-448；(各分量输入,非饱和模式返回值)→饱和模式返回值。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
