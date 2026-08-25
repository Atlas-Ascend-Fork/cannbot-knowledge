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

- [LogicalXor接口](logical_xor_interface.md)（`related`）：factor 查询提供另一种 LogicalXor workspace 计算方式，可按 tiling 形态选择。
- [GetLogicalXorMaxMinTmpSize](get_logical_xor_max_min_tmp_size.md)（`same_topic`）：GetLogicalXorTmpBufferFactorSize 与《GetLogicalXorMaxMinTmpSize》的实质衔接是：factor 查询与 GetLogicalXorMaxMinTmpSize 是同一 LogicalXor 临时空间的两种 Host 侧规划方式，LogicalXor 接口页和算子卡说明该空间由逐元素逻辑异或直接消费。
- [LogicalXor](logical_xor.md)（`same_topic`）：GetLogicalXorTmpBufferFactorSize 与《LogicalXor》的实质衔接是：factor 查询与 GetLogicalXorMaxMinTmpSize 是同一 LogicalXor 临时空间的两种 Host 侧规划方式，LogicalXor 接口页和算子卡说明该空间由逐元素逻辑异或直接消费。
<!-- cannbot:related:end -->
