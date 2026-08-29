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

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：将bfloat16类型数据转换为浮点数，返回转换后的值。；float val_f32=__bfloat162float(val)。API 卡定义单值 BF16 到 float 转换，ForeachTan 950 的 BF16 route 直接以该 intrinsic 产生 tanf 的 FP32 输入，构成实现与接口的调用关系。
<!-- cannbot:related:end -->
