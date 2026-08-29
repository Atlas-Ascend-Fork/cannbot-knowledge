---
type: API
title: GetLogicalXorTmpBufferFactorSize
description: 获取LogicalXor接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalXor_interface/GetLogicalXorTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalXorTmpBufferFactorSize

获取LogicalXor接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetLogicalXorTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalXorMaxMinTmpSize](get_logical_xor_max_min_tmp_size.md)（`related`）：Factor 查询卡给出“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize”；MaxMin 查询卡说明“在minValue到maxValue范围内，临时空间越大性能越好。”，两者组成先确定允许空间范围、再由实际 currBuff 反推单次元素数的 Host Tiling 链。
- [LogicalXor](logical_xor.md)（`related`）：Factor 查询卡指出“获取LogicalXor接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。”；计算卡的调用参数规定“count为参与计算元素个数。”，前者正是为后者的 count 分块提供容量上限。
<!-- cannbot:related:end -->
