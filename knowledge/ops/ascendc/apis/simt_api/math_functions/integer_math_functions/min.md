---
type: API
title: min（整数数学函数）
description: 获取两个输入数据中的最小值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# min

通用最小值函数（模板重载）。获取两个输入数据中的最小值，支持 long long、long、int、short、char 及对应 unsigned 类型的重载。

函数原型示例：long long min(long long x, long long y)、int min(int x, int y)、unsigned int min(unsigned int x, unsigned int y) 等共 10 种重载。

参数 x、y 为源操作数。返回输入数据中的最小值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [Min](../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/min.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《min（整数数学函数）》说明获取两个输入数据中的最小值。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [max（整数数学函数）](max.md)（`related`）：max 与 min 共享整数输入和返回契约但选择相反极值，分支和 clamp 逻辑迁移时需成对核对。
- [umax（整数数学函数）](umax.md)（`related`）：umax（整数数学函数） 与《min（整数数学函数）》的实质衔接是：umax 与 ullmax/max/llmax 共享整数最大值操作，umin/min 是比较方向相反的配对入口；它们用于按有无符号和位宽选择正确标量函数。
- [AscMin](../../../simd_api/c_api/reg/arithmetic_compute/asc_min.md)（`same_topic`）：min（整数数学函数） 与《AscMin》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [AscMin](../../../simd_api/c_api/vector_compute/asc_min.md)（`same_topic`）：min（整数数学函数） 与《AscMin》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [Min](../../../simd_api/basic_api/memory_vector_compute/basic_arithmetic/min.md)（`same_topic`）：min（整数数学函数） 与《Min》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [llmin（整数数学函数）](llmin.md)（`same_topic`）：min（整数数学函数） 与《llmin（整数数学函数）》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [ullmin（整数数学函数）](ullmin.md)（`same_topic`）：min（整数数学函数） 与《ullmin（整数数学函数）》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
- [umin（整数数学函数）](umin.md)（`same_topic`）：min（整数数学函数） 与《umin（整数数学函数）》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
<!-- cannbot:related:end -->
