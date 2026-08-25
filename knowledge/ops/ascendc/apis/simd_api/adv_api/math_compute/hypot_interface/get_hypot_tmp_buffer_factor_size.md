---
type: API
title: GetHypotTmpBufferFactorSize
description: 获取Hypot接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Hypot_interface/GetHypotTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetHypotTmpBufferFactorSize

获取Hypot接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetHypotTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Hypot](hypot.md)（`related`）：GetHypotTmpBufferFactorSize 的输出专门用于按现有 currBuff 反推 Hypot 单次处理元素数，随后传给 Hypot 计算。
- [Hypot接口](hypot_interface.md)（`related`）：《GetHypotTmpBufferFactorSize》明确“获取Hypot接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetHypotMaxMinTmpSize](get_hypot_max_min_tmp_size.md)（`same_topic`）：《GetHypotTmpBufferFactorSize》明确“获取Hypot接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”；它与《GetHypotMaxMinTmpSize》的“在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
