---
type: API
title: Remainderf
description: 获取输入数据x除以y的余数。求余数时，商取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/remainderf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Remainderf

功能：获取输入数据x除以y的余数。求余数时，商取最接近x除以y浮点数结果的整数，当x除以y的浮点数结果与左右最接近的整数距离相等时，商取偶数。

函数原型：float remainderf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据x除以y的余数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Fmodf](fmodf.md)（`related`）：Remainderf 与 Fmodf 都返回 x/y 的浮点余数，但前者把商舍入到最近整数且 ties-to-even，后者直接截取商的整数部分；并列阅读可避免在负数和半整数商处误选接口。
- [Remquof](remquof.md)（`same_topic`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；Remainderf正文说明“使用最近整数且平局取偶的同一余数公式，但不额外输出商”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
<!-- cannbot:related:end -->
