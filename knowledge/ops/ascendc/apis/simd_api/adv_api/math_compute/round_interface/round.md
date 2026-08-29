---
type: API
title: Round
description: 将输入元素四舍五入到最接近的整数，小数部分为0.5时向偶数舍入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/Round.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Round

将输入元素四舍五入到最接近的整数（Round(3.5)=4.0, Round(-3.4)=-3.0），若恰好在两个整数中间（小数部分为0.5）则向偶数舍入。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRoundMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；srcTensor为输入操作数，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：只支持四舍五入到整数，不支持到小数，小数部分为0.5时向偶数舍入；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetRoundMaxMinTmpSize](get_round_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRoundMaxMinTmpSize获取。；host侧Tiling接口，用于获取Round接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；目标产生 Round 所需 workspace 上下界，焦点消费该 Tiling 结果配置临时空间。
<!-- cannbot:related:end -->
