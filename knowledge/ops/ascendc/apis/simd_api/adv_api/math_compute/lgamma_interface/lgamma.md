---
type: API
title: Lgamma
description: 按元素计算x的gamma函数的绝对值并求自然对数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/Lgamma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Lgamma

按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(|gamma(x)|)）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。

模板参数isReuseSource仅在float时生效，true表示允许复用srcTensor内存空间。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。；host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。Lgamma 的 sharedTmpBuffer 重载消费 Host Tiling 接口给出的容量上下界，二者构成明确的临时空间生产与消费合同。
- [GetLgammaTmpBufferFactorSize](get_lgamma_tmp_buffer_factor_size.md)（`related`）：参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。。因子接口把可用 UB 反推成 Lgamma 可处理 shape，Lgamma 的手工临时空间重载正是该容量规划的消费端。
- [Lgammaf](../../../../simt_api/math_functions/float_math_functions/lgammaf.md)（`same_topic`）：功能：获取输入数据x伽马值的绝对值并求自然对数。；按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(｜gamma(x)｜)）。模板参数T支持half/float。两卡核心数学对象均为 lgamma，分别覆盖 SIMT 标量 float 与高阶 LocalTensor 逐元素接口。
<!-- cannbot:related:end -->
