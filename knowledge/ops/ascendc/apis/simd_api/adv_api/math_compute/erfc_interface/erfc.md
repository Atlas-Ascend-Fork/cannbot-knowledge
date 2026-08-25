---
type: API
title: Erfc
description: 返回输入x的互补误差函数结果，积分区间为x到无穷大
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erfc_interface/Erfc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erfc

返回输入x的互补误差函数结果，积分区间为x到无穷大。由于Erfc函数没有初等函数表达方式，一般通过函数逼近（多项式逼近）方式计算。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetErfcMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：输入源数据需保持值域在[-inf, inf]，超出范围输出结果无效；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscendC GELU 三系数 erfc 在大值域 fp32 精度不足](../../../../../runbooks/precision/gelu_erfc_polynomial_precision_budget.md)（`exemplifies`）：本 Runbook 的精度变量是 erfc 多项式逼近；Erfc API 卡明确该函数通常由多项式逼近实现并给出输入与临时空间契约，提供标准接口参照。
- [GELU 负尾部用 erfc 形态避免大数相消](../../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：该精度卡说明 GELU 负尾用 Erfc 形式规避 1+erf 的消减，给出选择 Erfc 的明确数值稳定性理由。
- [GetErfcMaxMinTmpSize](get_erfc_max_min_tmp_size.md)（`related`）：Erfc 的 sharedTmpBuffer 需由 Host tiling 预算，GetErfcMaxMinTmpSize 给出最小/最大值并说明区间内空间越大性能越好，是计算接口的直接前置。
- [GetErfcTmpBufferFactorSize](get_erfc_tmp_buffer_factor_size.md)（`related`）：factor size 反推的最大元素数直接决定一次 Erfc 调用可处理的 tile。
- [Erfc接口](erfc_interface.md)（`same_topic`）：Erfc接口 与《Erfc》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
<!-- cannbot:related:end -->
