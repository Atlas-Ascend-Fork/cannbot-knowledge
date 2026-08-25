---
type: API
title: umax（整数数学函数）
description: 获取两个输入数据中的最大值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/umax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# umax

unsigned int 类型最大值函数。获取两个输入数据中的最大值。

函数原型：inline unsigned int umax(const unsigned int x, const unsigned int y)

参数 x、y 为源操作数。返回两者中的最大值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [min（整数数学函数）](min.md)（`related`）：umax（整数数学函数） 与《min（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
- [umin（整数数学函数）](umin.md)（`related`）：umax（整数数学函数） 与《umin（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
- [llmax（整数数学函数）](llmax.md)（`same_topic`）：umax（整数数学函数） 与《llmax（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
- [max（整数数学函数）](max.md)（`same_topic`）：umax（整数数学函数） 与《max（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
- [ullmax（整数数学函数）](ullmax.md)（`same_topic`）：umax（整数数学函数） 与《ullmax（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
<!-- cannbot:related:end -->
