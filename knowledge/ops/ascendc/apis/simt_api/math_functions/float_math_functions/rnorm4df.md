---
type: API
title: Rnorm4df
description: 获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rnorm4df.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rnorm4df

功能：获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。

函数原型：float rnorm4df(float a, float b, float c, float d)

参数：a（输入）源操作数，b（输入）源操作数，c（输入）源操作数，d（输入）源操作数。

返回值：a^2 + b^2 + c^2 + d^2的平方根的倒数。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Norm3df](norm3df.md)（`related`）：《Norm3df》说明获取输入数据a、b、c平方和的平方根。；《Rnorm4df》说明获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。。二者在Norm3df与Rnorm3df互为范数和倒数范数，Norm4df/Normf及对应倒数版本改变向量维度但复用同一稳定范数任务上存在可执行的直接衔接。
- [Norm4df](norm4df.md)（`related`）：Rnorm4df 返回四维范数的倒数，与 Norm4df 构成归一化时的直接计算链。
- [Normf](normf.md)（`related`）：Rnorm4df 为四标量平方和范数的倒数版本，与 Normf 的动态数组正向范数形成参数个数和输出方向的明确接口对照。
- [Rnorm3df](rnorm3df.md)（`related`）：“Rnorm3df”定义：获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。；“Rnorm4df”定义：获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。。实质衔接：Norm3df 给出同三输入范数，焦点取其倒数；Rnorm4df 和 Rnormf 分别扩展固定四输入与数组长度，便于按数据组织选择。
- [Rnormf](rnormf.md)（`same_topic`）：Rnorm4df说明获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。
<!-- cannbot:related:end -->
