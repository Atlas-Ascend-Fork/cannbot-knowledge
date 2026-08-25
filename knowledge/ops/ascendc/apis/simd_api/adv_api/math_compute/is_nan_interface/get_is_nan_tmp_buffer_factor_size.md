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

- [IsNan](is_nan.md)（`related`）：该 factor 查询用于计算 IsNan Kernel 所需的 sharedTmpBuffer，直接服务于 IsNan 调用的工作空间规划。
- [GetIsNanMaxMinTmpSize](get_is_nan_max_min_tmp_size.md)（`same_topic`）：《GetIsNanMaxMinTmpSize》处理“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”。《GetIsNanTmpBufferFactorSize》明确提供“获取IsNan接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，其参数、调用或验证步骤直接接入IsNan 的临时空间计算、Kernel 调用和 SIMT 对应实现。
- [IsNan接口](is_nan_interface.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《GetIsNanTmpBufferFactorSize》提供“获取IsNan接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
<!-- cannbot:related:end -->
