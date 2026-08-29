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

- [GetErfcMaxMinTmpSize](get_erfc_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Erfc接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；临时空间大小通过GetErfcMaxMinTmpSize获取。。前者给出 Erfc 的 Host 侧 workspace 上下界，后者把它指定为 Erfc 计算重载的临时空间来源，二者构成 Tiling 尺寸规划到 Kernel 调用的直接前置链。
- [GetErfcTmpBufferFactorSize](get_erfc_tmp_buffer_factor_size.md)（`related`）：获取Erfc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。。FactorSize 卡把可用临时空间反推为单次 Erfc 元素数，Erfc 卡说明计算重载如何传入或申请 sharedTmpBuffer；联合阅读可在固定 UB 预算下确定分块规模。
<!-- cannbot:related:end -->
