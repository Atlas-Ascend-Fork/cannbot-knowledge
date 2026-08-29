---
type: API
title: GetMeanTmpBufferFactorSize
description: 获取maxLiveNodeCnt和extraBuf，用于推算Mean接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Mean_interface/GetMeanTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetMeanTmpBufferFactorSize

获取Mean接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetMeanTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize。maxLiveNodeCount可能为0，需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Mean](mean.md)（`related`）：获取Mean接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetMeanMaxMinTmpSize获取。。factor 查询把固定缓冲换算为 Mean 单次元素数，Mean 接口选择显式缓冲或框架申请，闭合 Kernel 侧空间规划。
<!-- cannbot:related:end -->
