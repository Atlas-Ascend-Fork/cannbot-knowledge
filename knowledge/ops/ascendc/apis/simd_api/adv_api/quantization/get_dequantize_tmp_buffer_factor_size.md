---
type: API
title: GetDequantizeTmpBufferFactorSize
description: 获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetDequantizeTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetDequantizeTmpBufferFactorSize

获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetDequantizeTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Dequantize](dequantize.md)（`related`）：获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。。前者用 maxLiveNodeCount 与 extraBuf 反推 Dequantize 单次可处理规模，后者给出被规划的反量化核心计算，二者可用于固定 UB 预算下确定一次 Dequantize 调用的数据量。
- [GetDequantizeMaxMinTmpSize](get_dequantize_max_min_tmp_size.md)（`related`）：“参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Dequantize接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。”与“获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。”。两卡分别给出空间上下界和固定空间反推处理元素数的 factor，形成互补 Tiling 预算。
<!-- cannbot:related:end -->
