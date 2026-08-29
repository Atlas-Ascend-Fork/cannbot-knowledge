---
type: API
title: GetLogicalAndsTmpBufferFactorSize
description: 获取LogicalAnds接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalAnds_interface/GetLogicalAndsTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalAndsTmpBufferFactorSize

获取LogicalAnds接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetLogicalAndsTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalAndsMaxMinTmpSize](get_logical_ands_max_min_tmp_size.md)（`related`）：获取LogicalAnds接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；host侧Tiling接口，用于获取LogicalAnds接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；factor 接口按固定临时空间反推单次元素数，max/min 接口给出可选临时空间区间，二者共同闭合 Host Tiling 容量计算。
- [LogicalAnds](logical_ands.md)（`related`）：输入矢量每个元素与标量进行逻辑与操作。当数据类型不是bool时，零视为False，非零视为True。；获取LogicalAnds接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。后者把固定缓冲预算换算为前者一次可处理的元素量。
<!-- cannbot:related:end -->
