---
type: API
title: ullmax（整数数学函数）
description: 获取两个输入数据中的最大值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/ullmax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ullmax

unsigned long long 类型最大值函数。获取两个输入数据中的最大值。

函数原型：inline unsigned long long int ullmax(const unsigned long long int x, const unsigned long long int y)

参数 x、y 为源操作数。返回两者中的最大值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [ullmin（整数数学函数）](ullmin.md)（`related`）：ullmax 选择相反极值，与 ullmin 共享输入类型，可用于范围 clamp 的上下界。
- [llmax（整数数学函数）](llmax.md)（`same_topic`）：llmax（整数数学函数） 与《ullmax（整数数学函数）》的衔接是：ullmax、llmin 和整数 max 与 llmax 直接对比符号性、运算方向及位宽，能确定边界值的选择语义。
- [umax（整数数学函数）](umax.md)（`same_topic`）：umax（整数数学函数） 与《ullmax（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
<!-- cannbot:related:end -->
