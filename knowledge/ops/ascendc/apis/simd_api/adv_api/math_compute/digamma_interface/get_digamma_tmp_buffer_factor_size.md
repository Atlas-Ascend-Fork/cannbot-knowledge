---
type: API
title: GetDigammaTmpBufferFactorSize
description: 获取Digamma接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Digamma_interface/GetDigammaTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetDigammaTmpBufferFactorSize

获取Digamma接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。最大临时空间与输入空间关系：maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer。

函数原型：void GetDigammaTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数（最大临时空间是输入所占空间的倍数）；extraBuffer输出额外临时空间大小（字节）。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Digamma](digamma.md)（`same_topic`）：GetDigammaTmpBufferFactorSize：该因子接口与 Digamma计算及同名 MaxMinTmpSize共同闭合 host预算公式和 kernel sharedTmpBuffer；接口页给出两种重载与复用约束。 目标卡《Digamma》补充：按元素计算x的gamma函数的对数导数
- [Digamma接口](digamma_interface.md)（`same_topic`）：GetDigammaTmpBufferFactorSize：该因子接口与 Digamma计算及同名 MaxMinTmpSize共同闭合 host预算公式和 kernel sharedTmpBuffer；接口页给出两种重载与复用约束。 目标卡《Digamma接口》补充：按元素计算x的gamma函数的对数导数（Digamma函数），并提供临时空间大小获取接口。
- [GetDigammaMaxMinTmpSize](get_digamma_max_min_tmp_size.md)（`same_topic`）：GetDigammaTmpBufferFactorSize：该因子接口与 Digamma计算及同名 MaxMinTmpSize共同闭合 host预算公式和 kernel sharedTmpBuffer；接口页给出两种重载与复用约束。 目标卡《GetDigammaMaxMinTmpSize》补充：在host侧获取Digamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
<!-- cannbot:related:end -->
