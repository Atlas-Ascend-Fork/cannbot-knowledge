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

- [Digamma](digamma.md)（`related`）：“获取Digamma接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。”提供固定 buffer 的反向容量公式；“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。”说明 Digamma 的临时空间入口，联合阅读可从已有 UB 容量推导可处理元素数。
- [GetDigammaMaxMinTmpSize](get_digamma_max_min_tmp_size.md)（`related`）：“在minValue到maxValue范围内，临时空间越大性能越好”；“用于在固定临时空间下推算算子单次最大计算元素数量”。前者给可选空间范围，后者把实际可用空间反算为分块元素数，形成 Tiling 决策链。
<!-- cannbot:related:end -->
