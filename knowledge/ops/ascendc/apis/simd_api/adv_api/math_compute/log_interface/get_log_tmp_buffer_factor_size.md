---
type: API
title: GetLogTmpBufferFactorSize
description: 获取Log/Log2/Log10接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/GetLogTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLogTmpBufferFactorSize

获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

提供三个重载：GetLogTmpBufferFactorSize、GetLog2TmpBufferFactorSize、GetLog10TmpBufferFactorSize，函数原型均为：void Get{Log|Log2|Log10}TmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当前Log接口（含Log2/Log10）不需要extraBuf；maxLiveNodeCount当前仅Log2接口src类型为half时需要；当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。
