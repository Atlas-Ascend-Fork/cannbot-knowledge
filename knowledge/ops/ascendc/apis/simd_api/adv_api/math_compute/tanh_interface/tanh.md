---
type: API
title: Tanh
description: 按元素做双曲正切函数计算，支持直接计算和误差补偿两种算法。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tanh_interface/Tanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Tanh

按元素做逻辑回归Tanh计算（y = (e^(2x)-1)/(e^(2x)+1)）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanhMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可；config为TanhConfig类型，其中algo指定算法：INTRINSIC（默认，直接按公式计算，性能更好）或SUBSECTION_COMPENSATION（误差补偿实现，精度更高）。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetTanhMaxMinTmpSize](get_tanh_max_min_tmp_size.md)（`related`）：Host 接口说明“host侧Tiling接口，用于获取Tanh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；Tanh 卡明确“临时空间大小通过GetTanhMaxMinTmpSize获取。”，两端形成 Tanh sharedTmpBuffer 的容量选择与调用链，但 Host Tiling 规划和 Kernel 双曲正切计算是两个主题。
- [GetTanhTmpBufferFactorSize](get_tanh_tmp_buffer_factor_size.md)（`related`）：Factor 接口说明“获取Tanh接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。”；Tanh 卡说明“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。”，前者为后者显式缓冲、带 calCount 重载推导单次 tile 上限，属于 Host 推导到 Kernel 调用的跨主题任务链。
<!-- cannbot:related:end -->
