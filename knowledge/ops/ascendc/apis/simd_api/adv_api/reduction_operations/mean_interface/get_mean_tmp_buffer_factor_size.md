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

- [GetMeanMaxMinTmpSize](get_mean_max_min_tmp_size.md)（`same_topic`）：焦点处理Mean 的 workspace factor 推算；GetMeanMaxMinTmpSize正文界定“在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择”。候选是 Mean 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Mean](mean.md)（`same_topic`）：焦点处理Mean 的 workspace factor 推算；Mean正文界定“沿最后一轴对输入元素求平均值，最多支持二维输入”。候选是 Mean 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Mean接口](mean_interface.md)（`same_topic`）：GetMeanTmpBufferFactorSize说明获取maxLiveNodeCnt和extraBuf，用于推算Mean接口在固定临时空间下单次最大计算元素数量；对Mean接口而言，Mean 的末轴二维约束与 ReduceMean 的多维 AR/RA 模式不同；两组 workspace 查询决定各自的 Tiling 空间。
<!-- cannbot:related:end -->
