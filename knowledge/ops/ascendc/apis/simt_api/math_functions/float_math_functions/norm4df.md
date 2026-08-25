---
type: API
title: Norm4df
description: 获取输入数据a、b、c、d平方和的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/norm4df.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Norm4df

功能：获取输入数据a、b、c、d的平方和a^2 + b^2+ c^2+ d^2的平方根。

函数原型：float norm4df(float a, float b, float c, float d)

参数：a（输入）源操作数，b（输入）源操作数，c（输入）源操作数，d（输入）源操作数。

返回值：a^2 + b^2 + c^2 + d^2的平方根。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Normf](normf.md)（`related`）：Norm4df 是 Normf 的固定四分量版本，直接对 a、b、c、d 的平方和开方，可在 n=4 且输入已是标量时避免指针式接口。
- [Rnorm4df](rnorm4df.md)（`related`）：Rnorm4df 返回四维范数的倒数，与 Norm4df 构成归一化时的直接计算链。
- [Norm3df](norm3df.md)（`same_topic`）：Norm3df 与 Norm4df 仅输入分量数量不同，可按三维或四维向量长度选择。
- [Rnormf](rnormf.md)（`same_topic`）：Norm4df说明获取输入数据a、b、c、d平方和的平方根。
<!-- cannbot:related:end -->
