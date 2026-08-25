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

- [GetLogicalOrsMaxMinTmpSize](get_logical_ors_max_min_tmp_size.md)（`same_topic`）：《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递；《GetLogicalOrsTmpBufferFactorSize》说明获取LogicalOrs接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。二者在LogicalOrs的Host侧最大/最小临时空间与factor查询共同为同一个Kernel接口确定workspace预算上存在可执行的直接衔接。
- [LogicalOrs](logical_ors.md)（`same_topic`）：LogicalOrs 与《GetLogicalOrsTmpBufferFactorSize》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [LogicalOrs接口](logical_ors_interface.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《GetLogicalOrsTmpBufferFactorSize》说明获取LogicalOrs接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
