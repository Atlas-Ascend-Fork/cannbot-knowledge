---
type: API
title: GetRoundTmpBufferFactorSize
description: 获取Round接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/GetRoundTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetRoundTmpBufferFactorSize

获取Round接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetRoundTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetRoundMaxMinTmpSize](get_round_max_min_tmp_size.md)（`same_topic`）：host侧Tiling接口，用于获取Round接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。 获取Round接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。 一个从 shape 求空间区间，一个从固定空间预算反推处理规模，是 Round Host Tiling 的两种互补容量计算。
<!-- cannbot:related:end -->
