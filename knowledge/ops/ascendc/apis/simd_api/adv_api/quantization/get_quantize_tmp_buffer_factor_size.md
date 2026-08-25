---
type: API
title: GetQuantizeTmpBufferFactorSize
description: 获取Quantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetQuantizeTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetQuantizeTmpBufferFactorSize

获取Quantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetQuantizeTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetQuantizeMaxMinTmpSize](get_quantize_max_min_tmp_size.md)（`same_topic`）：GetQuantizeTmpBufferFactorSize 与《GetQuantizeMaxMinTmpSize》的实质衔接是：GetQuantizeTmpBufferFactorSize 用可用 UB 反推 Quantize 的单次元素数，GetQuantizeMaxMinTmpSize 给出另一种 Host 侧空间选择，Quantize kernel 是两类查询结果的直接消费方。
- [Quantize](quantize.md)（`same_topic`）：GetQuantizeTmpBufferFactorSize 与《Quantize》的实质衔接是：GetQuantizeTmpBufferFactorSize 用可用 UB 反推 Quantize 的单次元素数，GetQuantizeMaxMinTmpSize 给出另一种 Host 侧空间选择，Quantize kernel 是两类查询结果的直接消费方。
<!-- cannbot:related:end -->
