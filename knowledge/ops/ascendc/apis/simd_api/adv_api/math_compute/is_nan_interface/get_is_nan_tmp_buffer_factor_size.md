---
type: API
title: GetIsNanTmpBufferFactorSize
description: 获取IsNan接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsNan_interface/GetIsNanTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetIsNanTmpBufferFactorSize

获取IsNan接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetIsNanTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetIsNanMaxMinTmpSize](get_is_nan_max_min_tmp_size.md)（`related`）：获取IsNan接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；host侧Tiling接口，用于获取IsNan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两接口分别从固定临时空间反推单次元素量、按输入 shape 求临时空间上下界，共同完成 IsNan 的 Host Tiling 容量决策。
- [IsNan](is_nan.md)（`related`）：参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetIsNanMaxMinTmpSize获取。。前者给出固定临时空间下 IsNan 单次处理量的反推公式，后者是实际消费 sharedTmpBuffer 的逐元素 NaN 判断接口。
<!-- cannbot:related:end -->
