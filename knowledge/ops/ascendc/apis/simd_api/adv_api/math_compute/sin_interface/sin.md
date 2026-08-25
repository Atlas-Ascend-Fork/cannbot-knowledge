---
type: API
title: Sin
description: 按元素对输入数据做正弦函数计算，支持多项式逼近和周期约减两种算法。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sin_interface/Sin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Sin

按元素做正弦函数计算，基于泰勒展开式实现。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetSinMaxMinTmpSize获取。

模板参数isReuseSource仅在float时生效，true表示允许复用srcTensor内存空间；config为SinConfig类型，其中algo指定算法：POLYNOMIAL_APPROXIMATION（默认，多项式逼近，输入值域[-65504.0, 65504.0]）或RADIAN_REDUCTION（周期约减，支持输入全值域）。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：使用POLYNOMIAL_APPROXIMATION算法时，Ascend 950PR/950DT、A3、A2训练/推理、推理AI Core产品的输入源数据值域必须在[-65504.0, 65504.0]范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [按序列位缓存 cos/sin 并让 q/k 共享搬运](../../../../../runbooks/performance/cache_position_coefficients_across_shared_inputs.md)（`exemplifies`）：Sin 与《按序列位缓存 cos/sin 并让 q/k 共享搬运》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Cos](../cos_interface/cos.md)（`related`）：Sin 与《Cos》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Cos接口](../cos_interface/cos_interface.md)（`related`）：Sin 与《Cos接口》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Tan](../tan_interface/tan.md)（`related`）：Sin/Cos 组合可做公式 A/B，但不能忽略极点边界。
- [GetSinMaxMinTmpSize](get_sin_max_min_tmp_size.md)（`same_topic`）：Sin 与《GetSinMaxMinTmpSize》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [GetSinTmpBufferFactorSize](get_sin_tmp_buffer_factor_size.md)（`same_topic`）：Sin 与《GetSinTmpBufferFactorSize》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Sin接口](sin_interface.md)（`same_topic`）：Sin 与《Sin接口》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Tan接口](../tan_interface/tan_interface.md)（`same_topic`）：Tan接口 与《Sin》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
