---
type: API
title: GetAscendAntiQuantTmpBufferFactorSize
description: 获取AscendAntiQuant接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetAscendAntiQuantTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetAscendAntiQuantTmpBufferFactorSize

获取AscendAntiQuant接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetAscendAntiQuantTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [AscendAntiQuant](ascend_anti_quant.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“接口参数包含dstTensor输出、srcTensor输入（shape ［m,n］）、scale/offset量化系数（shape因策略而异）、sharedTmpBuffer临时缓存、params参数信息。”。factor 接口把可用缓冲换算为 currentShapeSize，AscendAntiQuant 计算接口实际消费 sharedTmpBuffer。
- [GetAscendAntiQuantMaxMinTmpSize](get_ascend_anti_quant_max_min_tmp_size.md)（`related`）：“调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。”；“isReuseSource与AscendAntiQuant接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。”。两张卡是同一 AscendAntiQuant Tiling 中 factor 反推和 max/min 容量边界的互补接口。
<!-- cannbot:related:end -->
