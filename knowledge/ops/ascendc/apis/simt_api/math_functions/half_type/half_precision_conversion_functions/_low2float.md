---
type: API
title: __low2float
description: 将输入数据的低16位转换为浮点数并返回结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__low2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __low2float

功能：将输入数据的低16位转换为浮点数并返回结果。

函数原型：float __low2float(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的低16位转换为浮点数的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Float](../../../../simd_api/c_api/reg/data_type_convert/asc_half2float.md)（`related`）：AscHalf2Float 提供 Reg C API 的 half→float 向量转换，而 __low2float 是 SIMT packed 值的低 lane 标量提取，二者是迁移执行模型时的互补路径。
- [__low2float](../../bfloat16_type/bfloat16_precision_conversion_functions/_low2float.md)（`related`）：两接口都从 packed 16 位双元素中提取低 lane 并升为 float，分别对应 half2 与 bfloat16x2。
- [__low2half](_low2half.md)（`related`）：__low2float 同样读取 half2 低 16 位，但进行数值提升到 float；只取位域与取后转换不可混同。
<!-- cannbot:related:end -->
