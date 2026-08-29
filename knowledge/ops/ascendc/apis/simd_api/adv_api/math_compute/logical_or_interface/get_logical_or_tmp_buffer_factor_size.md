---
type: API
title: GetLogicalOrTmpBufferFactorSize
description: 获取LogicalOr接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOr_interface/GetLogicalOrTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalOrTmpBufferFactorSize

获取LogicalOr接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetLogicalOrTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalOrMaxMinTmpSize](get_logical_or_max_min_tmp_size.md)（`related`）：获取LogicalOr接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；host侧Tiling接口，用于获取LogicalOr接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两个 Host 接口面向同一 LogicalOr 临时空间预算：FactorSize 将固定空间换算为单次元素量，MaxMin 给出可选空间上下界。
- [LogicalOr](logical_or.md)（`related`）：获取LogicalOr接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素进行逻辑或操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。。FactorSize 的输出专门用于规划 LogicalOr 单次计算量，LogicalOr 页定义被规划的 Kernel 运算及平台范围。
<!-- cannbot:related:end -->
