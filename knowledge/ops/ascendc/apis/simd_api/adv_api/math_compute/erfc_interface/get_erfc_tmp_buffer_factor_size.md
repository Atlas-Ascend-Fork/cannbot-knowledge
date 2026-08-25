---
type: API
title: GetErfcTmpBufferFactorSize
description: 获取Erfc接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erfc_interface/GetErfcTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetErfcTmpBufferFactorSize

获取Erfc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetErfcTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Erfc](erfc.md)（`related`）：factor size 反推的最大元素数直接决定一次 Erfc 调用可处理的 tile。
- [Erfc接口](erfc_interface.md)（`same_topic`）：Erfc接口 与《GetErfcTmpBufferFactorSize》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
- [GetErfcMaxMinTmpSize](get_erfc_max_min_tmp_size.md)（`same_topic`）：MaxMin 从 shape 给出 Erfc sharedTmpBuffer 合法区间，FactorSize 从固定剩余空间反推 currentShapeSize；二者是同一临时空间的正向预算和反向容量计算。
<!-- cannbot:related:end -->
