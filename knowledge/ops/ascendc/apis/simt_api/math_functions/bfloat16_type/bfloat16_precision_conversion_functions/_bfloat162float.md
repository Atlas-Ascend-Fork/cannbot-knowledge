---
type: API
title: __bfloat162float
description: 将bfloat16类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162float

将bfloat16类型数据转换为浮点数，返回转换后的值。
函数原型：float __bfloat162float(const bfloat16_t x)
返回值：输入转换为浮点数的结果。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Float](../../../../simd_api/c_api/reg/data_type_convert/asc_bfloat162float.md)（`related`）：C Reg AscBfloat162Float 与 SIMT 标量函数实现同一数值提升，可按执行模型选型。
- [AscBfloat162float](../../../../simd_api/c_api/vector_compute/asc_bfloat162float.md)（`related`）：Vector C API 提供 UB 批量 bfloat16→float，可与 SIMT 标量版本按访存布局和并行模型选择。
- [__bfloat1622float2](_bfloat1622float2.md)（`related`）：“__bfloat1622float2”处理将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。；“__bfloat162float”明确将bfloat16类型数据转换为浮点数，返回转换后的值。。实质衔接：float2 与 bfloat16x2 的反向转换说明向量打包路径，标量 bfloat16→float 用于核对每个分量的转换语义。
- [__low2float](_low2float.md)（`same_topic`）：__low2float 与《__bfloat162float》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
<!-- cannbot:related:end -->
