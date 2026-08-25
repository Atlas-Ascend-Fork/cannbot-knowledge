---
type: API
title: Frac
description: 按元素做取小数计算，返回输入数据的小数部分，支持half和float数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Frac_interface/Frac.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Frac

按元素做取小数计算，返回输入数据的小数部分（Frac(-258.41888)=-0.41888428, Frac(5592.625)=0.625）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetFracMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：针对Atlas 推理系列产品AI Core输入数据限制在[-2147483647.0, 2147483647.0]；不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetFracMaxMinTmpSize](get_frac_max_min_tmp_size.md)（`related`）：GetFracMaxMinTmpSize 返回的 min/max 是 Frac kernel sharedTmpBuffer 的正确性和性能边界，直接用于 host tiling 选值。
- [GetFracTmpBufferFactorSize](get_frac_tmp_buffer_factor_size.md)（`related`）：固定 UB 预算时，Factor 查询用 maxLiveNodeCount 和 extraBuf 反推 Frac 单次最大元素数，并规定不足 256B 时向上取整。
- [Trunc接口](../trunc_interface/trunc_interface.md)（`related`）：Frac 返回带符号小数部分，而 Trunc 定义向零取整；用 x-Trunc(x) 可构造与 Frac(-x) 符号一致的独立 oracle。
- [Frac接口](frac_interface.md)（`same_topic`）：《Frac》明确“按元素做取小数计算，返回输入数据的小数部分，支持half和float数据类型。”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
