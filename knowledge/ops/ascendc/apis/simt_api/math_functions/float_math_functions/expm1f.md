---
type: API
title: Expm1f
description: 指定输入x，获取e的x次方减1。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expm1f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Expm1f

功能：指定输入x，获取e的x次方减1。

函数原型：float expm1f(float x)

参数：x（输入）源操作数。

返回值：e的x次方减1。特殊值：inf→inf；-inf→-1.0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持输入为Subnormal的场景：本接口内部实现使用到了expf，由于expf不支持Subnormal场景，当输入x处于Subnormal范围内时，返回值为0；当x为较大负数且expf的结果处于Subnormal范围内时，本接口最终结果为-1.0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Expm1 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/expm1_950.md)（`related`）：算子卡明确“对 `｜x｜ > 2` 直接采用 `expm1f(x)`”；API 卡定义“功能：指定输入x，获取e的x次方减1。”并列出 950 的 subnormal 边界，直接支撑大输入分支及其特殊值核对。
- [InplaceExpm1 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_expm1_950.md)（`related`）：SIMT body 对每个 FP32 元素先保留库函数 `expm1f(x)` 结果。`｜x｜ <= 2` 时使用源码中的 ln2 约化、五阶系数组合及 `exp2f` 重建；`｜x｜ > 2` 时选回 `expm1f`。；函数原型：float expm1f(float x)；算子核心在大幅值分支直接消费 SIMT expm1f，API 卡提供该调用的标量合同。
<!-- cannbot:related:end -->
