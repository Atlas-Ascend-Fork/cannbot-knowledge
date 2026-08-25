---
type: API
title: Hypot
description: 按元素计算两个浮点数平方和的平方根
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Hypot_interface/Hypot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hypot

按元素计算两个浮点数平方和的平方根（dst = sqrt(src0^2 + src1^2)，Hypot(3.0, 4.0)=5.0）。模板参数T支持half/bfloat16_t/float。仅Ascend 950PR/950DT支持。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetHypotMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；src0Tensor、src1Tensor为两个输入源操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：src0Tensor与src1Tensor数据长度必须一致；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束；输入中任意一个或多个为inf时对应位置输出inf；输入中任意一个或多个为nan且该位置都不是inf时对应位置输出nan。

<!-- cannbot:related:start -->
## 相关

- [GetHypotMaxMinTmpSize](get_hypot_max_min_tmp_size.md)（`related`）：The query determines the minimum and maximum temporary buffer accepted by the Hypot kernel call.
- [GetHypotTmpBufferFactorSize](get_hypot_tmp_buffer_factor_size.md)（`related`）：GetHypotTmpBufferFactorSize 的输出专门用于按现有 currBuff 反推 Hypot 单次处理元素数，随后传给 Hypot 计算。
- [Hypotf](../../../../simt_api/math_functions/float_math_functions/hypotf.md)（`related`）：Hypotf 与《Hypot》的实质衔接是：rhypotf 是 hypotf 的倒数形式，高阶 Hypot 是张量级等价运算，二者直接支撑算法替换和接口选型。
- [Hypot接口](hypot_interface.md)（`same_topic`）：《Hypot》明确“按元素计算两个浮点数平方和的平方根”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
