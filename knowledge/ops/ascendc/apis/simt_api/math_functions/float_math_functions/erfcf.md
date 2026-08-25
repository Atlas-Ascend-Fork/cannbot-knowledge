---
type: API
title: Erfcf
description: 获取输入数据的互补误差函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/erfcf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Erfcf

功能：获取输入数据的互补误差函数值。

函数原型：float erfcf(float x)

参数：x（输入）源操作数。

返回值：当x为nan时，返回值为nan；当x为inf时，返回值为0；当x为-inf时，返回值为2。特殊值：nan→nan；inf→0；-inf→2。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了exp2f，由于exp2f不支持Subnormal场景，在极少数场景下内部指数计算结果为Subnormal数据，导致本接口最终结果为0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [GELU 负尾部用 erfc 形态避免大数相消](../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：《GELU 负尾部用 erfc 形态避免大数相消》给出“fp32 exact GELU 用 0.5x 加减近等幅项会在负大值尾部相消；直接计算 max(x,0)-0.5|x|erfc(|x|/sqrt(2)) 后 20/20。”；该约束/探针可直接复现、解释或前置验证《Erfcf》中的“获取输入数据的互补误差函数值。”。
- [Erfcxf](erfcxf.md)（`related`）：Erfcxf is the scaled complementary error function, while Erfcf provides the unscaled value and different extreme-value behavior.
- [Erfc接口](../../../simd_api/adv_api/math_compute/erfc_interface/erfc_interface.md)（`same_topic`）：高阶 Erfc 对 LocalTensor 批量计算互补误差函数，SIMT erfc 对线程标量计算相同数学函数；两卡描述同一 erfc 数值语义，只是执行粒度不同。
<!-- cannbot:related:end -->
