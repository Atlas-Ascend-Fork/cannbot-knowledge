---
type: API
title: ClampMin
description: 将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。 ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/ClampMin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# ClampMin

将srcTensor中小于scalar的元素替换为scalar，大于等于scalar的元素保持不变，输出到dstTensor。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer入参传入临时空间（开发者自行管理，可复用，内存利用率高），或由接口框架申请临时空间（需预留空间，大小通过GetClampMaxMinTmpSize获取）。接口内部涉及复杂数学计算，需要额外临时空间存储中间变量。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；scalar为下限阈值，类型与srcTensor一致；calCount为参与计算的元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer入参传入临时空间（开发者自行管理，可复用，内存利用率高），或由接口框架申请临时空间（需预留空间，大小通过GetClampMaxMinTmpSize获取）。；host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ClampMin 的框架申请重载明确使用右侧公共接口确定预留大小，但右侧还覆盖另外两个 Clamp 操作，所以保持相关关系。
<!-- cannbot:related:end -->
