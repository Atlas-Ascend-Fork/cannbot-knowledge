---
type: API
title: Rnorm3df
description: 获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rnorm3df.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rnorm3df

功能：获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。

函数原型：float rnorm3df(float a, float b, float c)

参数：a（输入）源操作数，b（输入）源操作数，c（输入）源操作数。

返回值：a^2 + b^2 + c^2的平方根的倒数。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Norm3df](norm3df.md)（`related`）：《Norm3df》说明获取输入数据a、b、c平方和的平方根。；《Rnorm3df》说明获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。。二者在Norm3df与Rnorm3df互为范数和倒数范数，Norm4df/Normf及对应倒数版本改变向量维度但复用同一稳定范数任务上存在可执行的直接衔接。
- [Normf](normf.md)（`related`）：Rnorm3df 把固定三个标量的平方和开方后再取倒数，可与 Normf/Norm3df 区分动态长度、固定长度以及是否取倒数三类选择。
- [Rnorm4df](rnorm4df.md)（`related`）：“Rnorm3df”定义：获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。；“Rnorm4df”定义：获取输入数据a、b、c、d的平方和a^2 + b^2 + c^2 + d^2的平方根的倒数。。实质衔接：Norm3df 给出同三输入范数，焦点取其倒数；Rnorm4df 和 Rnormf 分别扩展固定四输入与数组长度，便于按数据组织选择。
- [Rnormf](rnormf.md)（`related`）：“Rnorm3df”定义：获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根的倒数。；“Rnormf”定义：获取输入数据a中前n个元素的平方和a\[0\]^2 + a\[1\]^2 + ...+ a\[n-1\]^2的平方根的倒数。。实质衔接：Norm3df 给出同三输入范数，焦点取其倒数；Rnorm4df 和 Rnormf 分别扩展固定四输入与数组长度，便于按数据组织选择。
<!-- cannbot:related:end -->
