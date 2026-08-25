---
type: API
title: llmin（整数数学函数）
description: 获取两个输入数据中的最小值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/llmin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# llmin

long long 类型最小值函数。获取两个输入数据中的最小值。

函数原型：inline long long int llmin(const long long int x, const long long int y)

参数 x、y 为源操作数。返回两者中的最小值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [llmax（整数数学函数）](llmax.md)（`same_topic`）：llmax（整数数学函数） 与《llmin（整数数学函数）》的衔接是：ullmax、llmin 和整数 max 与 llmax 直接对比符号性、运算方向及位宽，能确定边界值的选择语义。
- [min（整数数学函数）](min.md)（`same_topic`）：min（整数数学函数） 与《llmin（整数数学函数）》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [ullmin（整数数学函数）](ullmin.md)（`same_topic`）：两卡执行同一二元最小值，只差 long long 与 unsigned long long；需要按符号解释选择，尤其高位为 1 时结果不同。
<!-- cannbot:related:end -->
