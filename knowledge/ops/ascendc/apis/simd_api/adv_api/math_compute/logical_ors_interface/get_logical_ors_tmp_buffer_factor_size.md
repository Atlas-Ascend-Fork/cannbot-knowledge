---
type: API
title: GetLogicalOrsTmpBufferFactorSize
description: 获取LogicalOrs接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOrs_interface/GetLogicalOrsTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalOrsTmpBufferFactorSize

获取LogicalOrs接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetLogicalOrsTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalOrsMaxMinTmpSize](get_logical_ors_max_min_tmp_size.md)（`related`）：焦点接口给出“在minValue到maxValue范围内，临时空间越大性能越好。”的分配区间；目标接口给出“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize”，可在固定 UB 预算下反推单次 shape，两者是 LogicalOrs Host Tiling 的正向预算与反向求块配套合同。
- [LogicalOrs](logical_ors.md)（`related`）：输入矢量每个元素与标量进行逻辑或操作。；获取LogicalOrs接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。。计算接口定义 LogicalOrs 的逐元素逻辑或语义，固定临时空间时该接口给出反推单次处理元素数的因子。
<!-- cannbot:related:end -->
