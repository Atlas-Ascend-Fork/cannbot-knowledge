---
type: API
title: __half2float
description: 将half类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2float

功能：将half类型数据转换为浮点数，返回转换后的值。

函数原型：float __half2float(const half x)

参数：x（输入）源操作数。

返回值：输入转换成的浮点数。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“float val_f32=__half2float(val)”是 FP16 route 进入 tanf 前的实际转换；“功能：将half类型数据转换为浮点数，返回转换后的值。”给出扩精度方向。
- [AscHalf2Float](../../../../simd_api/c_api/reg/data_type_convert/asc_half2float.md)（`same_topic`）：将half类型数据转换为float类型，无舍入模式。；功能：将half类型数据转换为浮点数，返回转换后的值。两页定义相同 half 到 float 转换语义，分别提供 Reg C API 与 SIMT 函数形式，便于按编程模型选接口。
<!-- cannbot:related:end -->
