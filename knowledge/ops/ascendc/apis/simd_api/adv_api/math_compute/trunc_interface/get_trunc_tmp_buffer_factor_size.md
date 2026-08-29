---
type: API
title: GetTruncTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/GetTruncTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTruncTmpBufferFactorSize

获取Trunc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetTruncTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Trunc](trunc.md)（`same_topic`）：获取Trunc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素做浮点数截断，即向零取整操作（Trunc(3.9)=3, Trunc(-3.9)=-3）。模板参数T支持half/float。；factor 查询依据固定空间推导 Trunc 单次 calCount，计算卡以该 calCount 对 half 或 float 执行向零取整。
<!-- cannbot:related:end -->
