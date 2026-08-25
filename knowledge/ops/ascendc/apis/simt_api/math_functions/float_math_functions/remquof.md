---
type: API
title: Remquof
description: 获取输入数据x除以y的余数r。r=x-ny，其中n是x除以y的商，n取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数，同时将商赋值给指针变量quo。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/remquof.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Remquof

功能：获取输入数据x除以y的余数r。r=x-ny，其中n是x除以y的商，n取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数，同时将商赋值给指针变量quo。

函数原型：float remquof(float x, float y, int *quo)

参数：x（输入）源操作数，y（输入）源操作数，quo（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储除法运算的商。

返回值：输入数据x除以y的余数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Fmodf](fmodf.md)（`related`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；Fmodf正文说明“同为浮点余数，但商向零截断；与 Remquof 的最近偶数商构成关键选择边界”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
- [Remainderf](remainderf.md)（`same_topic`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；Remainderf正文说明“使用最近整数且平局取偶的同一余数公式，但不额外输出商”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
- [float类型数学库函数](float_math_functions.md)（`same_topic`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；float类型数学库函数正文说明“提供 float 数学函数族入口，并在列表中明确收录 Remquof”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
<!-- cannbot:related:end -->
