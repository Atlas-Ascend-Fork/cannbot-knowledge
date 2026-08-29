---
type: API
title: 数学函数expf
description: 根据输入x，获取e的x次方的计算结果。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数expf

功能：根据输入x，获取e的x次方的计算结果。

函数原型：float expf(float x)

参数：x（输入）源操作数，数据类型为float。

返回值：e的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachExp 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_exp_950.md)（`related`）：ForeachExp950 的 R-001 路线是“FLOAT32 值直接传给 `expf`”；expf API执行“根据输入x，获取e的x次方的计算结果。”。API语义支撑每线程标量指数计算和特殊值验证。
- [ForeachSigmoid 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_sigmoid_950.md)（`related`）：功能：根据输入x，获取e的x次方的计算结果。；`ComputeSigmoid` 无论 T 为 half、float 还是 BF16，都先转 float，按 `-x -> expf -> +1 -> reciprocal` 计算，再 cast 回 T。API 是 ForeachSigmoid 950 内部 sigmoid 标量链的核心函数。
<!-- cannbot:related:end -->
