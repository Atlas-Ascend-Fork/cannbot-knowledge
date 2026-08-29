---
type: API
title: GetLogicalAndTmpBufferFactorSize
description: 获取LogicalAnd接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalAnd_interface/GetLogicalAndTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetLogicalAndTmpBufferFactorSize

获取LogicalAnd接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetLogicalAndTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalAndMaxMinTmpSize](get_logical_and_max_min_tmp_size.md)（`related`）：获取LogicalAnd接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；host侧Tiling接口，用于获取LogicalAnd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两个 Host 侧接口共同完成 LogicalAnd 的临时空间规划：一个反推单次 shape，另一个给出可分配空间上下界。
- [LogicalAnd](logical_and.md)（`related`）：按元素进行逻辑与操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。；获取LogicalAnd接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。。LogicalAnd 是计算接口，Factor 接口直接为它在固定 sharedTmpBuffer 下反推单次处理元素数。
<!-- cannbot:related:end -->
