---
type: API
title: Exp
description: 按元素取自然指数，可选择是否使用泰勒展开公式进行计算
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/Exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Exp

按元素取自然指数e^x。可通过模板参数taylorExpandLevel选择是否使用泰勒展开公式：项数为0表示不使用泰勒公式，项数不为0时使用泰勒展开（将输入拆分为整数部分xA和小数部分xB分别处理）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetExpMaxMinTmpSize获取。

模板参数taylorExpandLevel为泰勒展开项数，取值范围[0, 255]，推荐[10, 15]；项数越多精度越高但性能越差，项数太少会有精度误差。isReuseSource仅在float时生效，true表示允许复用srcLocal内存空间。接口参数：dstLocal为输出操作数；srcLocal为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstLocal一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetExpMaxMinTmpSize](get_exp_max_min_tmp_size.md)（`related`）：“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetExpMaxMinTmpSize获取。”与“host侧Tiling接口，用于获取Exp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”。Exp 的 sharedTmpBuffer 重载需要空间预算，Host 接口给出可用最大值与不得低于的最小值。
- [GetExpTmpBufferFactorSize](get_exp_tmp_buffer_factor_size.md)（`related`）：“获取Exp接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。”提供反推 tile 容量的系数，而“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetExpMaxMinTmpSize获取。”说明 Exp 的临时空间消费入口；两者可用于在多个高阶 API 共用 UB 时确定 Exp 单次 calCount。
<!-- cannbot:related:end -->
