---
type: API
title: Normf
description: 获取输入数据a中前n个元素平方和的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/normf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Normf

功能：获取输入数据a中前n个元素的平方和a[0]^2 + a[1]^2 +...+ a[n-1]^2的平方根。

函数原型：float normf(int n, float* a)

参数：n（输入）源操作数。输入数据a中连续计算的元素个数，a（输入）源操作数。Unified Buffer、Global Memory或栈空间的地址。

返回值：a[0]^2 + a[1]^2 + ...+ a[n-1]^2的平方根。

约束：- 输入数据a的长度必须大于等于参数n。 - 若n过大，接口性能无法保证。 - 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当输入a的所有元素均为Subnormal数据时，会导致接口最终结果为nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Norm3df](norm3df.md)（`related`）：《Norm3df》说明获取输入数据a、b、c平方和的平方根。；《Normf》说明获取输入数据a中前n个元素平方和的平方根。。二者在Norm3df与Rnorm3df互为范数和倒数范数，Norm4df/Normf及对应倒数版本改变向量维度但复用同一稳定范数任务上存在可执行的直接衔接。
- [Norm4df](norm4df.md)（`related`）：Norm4df 是 Normf 的固定四分量版本，直接对 a、b、c、d 的平方和开方，可在 n=4 且输入已是标量时避免指针式接口。
- [Rnorm3df](rnorm3df.md)（`related`）：Rnorm3df 把固定三个标量的平方和开方后再取倒数，可与 Normf/Norm3df 区分动态长度、固定长度以及是否取倒数三类选择。
- [Rnorm4df](rnorm4df.md)（`related`）：Rnorm4df 为四标量平方和范数的倒数版本，与 Normf 的动态数组正向范数形成参数个数和输出方向的明确接口对照。
- [Rnormf](rnormf.md)（`related`）：Normf 与 Rnormf 都消费指针 a 的前 n 个元素并计算平方和；前者返回范数，后者返回其倒数，组成相同数组输入下的直接结果选择。
<!-- cannbot:related:end -->
