---
type: API
title: GetErfTmpBufferFactorSize
description: 获取Erf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/GetErfTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetErfTmpBufferFactorSize

获取Erf接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。

函数原型：void GetErfTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Erf](erf.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。”。factor 接口反推可计算元素规模，Erf 接口消费 sharedTmpBuffer 和 calCount，构成 Tiling 到计算调用的直接合同。
- [GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)（`related`）：“调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。”；“在minValue到maxValue范围内，临时空间越大性能越好。约束：无。”。两张卡提供 Erf 临时空间规划的两种互补合同：factor 路线反推共同 calCount，max/min 路线给出合法容量区间。
<!-- cannbot:related:end -->
