---
type: API
title: Sinhf
description: 获取输入数据的双曲正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sinhf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sinhf

功能：获取输入数据的双曲正弦值。

函数原型：float sinhf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲正弦值。特殊值：inf→inf；-inf→-inf；nan→nan；0→0。

约束：本接口支持的输入数据为[-89.4, 89.4]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachSinh 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_sinh_950.md)（`related`）：｜ 计算语义 ｜ 对 TensorList 每个 Tensor 逐元素计算 `sinh`；SIMT body 统一以 FP32 `sinhf` 求值。 ｜；功能：获取输入数据的双曲正弦值。；950 ForeachSinh 的 SIMT body 明确把每个元素交给 FP32 sinhf，API 卡因此直接补齐该叶子调用的输入范围、特殊值与必需头文件。
<!-- cannbot:related:end -->
