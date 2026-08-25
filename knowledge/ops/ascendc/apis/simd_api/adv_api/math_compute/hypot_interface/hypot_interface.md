---
type: API
title: Hypot接口
description: 按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Hypot_interface/Hypot_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hypot接口

按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。

按元素计算两个浮点数平方和的平方根。计算公式如下： 举例如下： Hypot(3.0, 4.0) = 5.0

本接口组包含 Hypot。

本接口属于高阶数学计算接口。

支持的数据类型为 half、bfloat16_t、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：源操作数src0Tensor与src1Tensor的数据长度必须保持一致。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数、目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetHypotMaxMinTmpSize](get_hypot_max_min_tmp_size.md)（`related`）：《GetHypotMaxMinTmpSize》明确“在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetHypotTmpBufferFactorSize](get_hypot_tmp_buffer_factor_size.md)（`related`）：《GetHypotTmpBufferFactorSize》明确“获取Hypot接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Hypotf](../../../../simt_api/math_functions/float_math_functions/hypotf.md)（`related`）：《Hypotf》明确“获取输入数据x、y平方和的平方根。”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Hypot](hypot.md)（`same_topic`）：《Hypot》明确“按元素计算两个浮点数平方和的平方根”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
