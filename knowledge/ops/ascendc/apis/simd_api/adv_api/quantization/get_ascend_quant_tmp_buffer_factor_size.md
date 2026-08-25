---
type: API
title: GetAscendQuantTmpBufferFactorSize
description: 获取AscendQuant接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetAscendQuantTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetAscendQuantTmpBufferFactorSize

获取AscendQuant接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetAscendQuantTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [AscendQuant](ascend_quant.md)（`same_topic`）：factor-size 依据固定空间反推 AscendQuant 单次处理量，与 max/min 查询共同完成分片设计。
- [GetAscendQuantMaxMinTmpSize](get_ascend_quant_max_min_tmp_size.md)（`same_topic`）：《GetAscendQuantMaxMinTmpSize》说明在host侧获取AscendQuant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。；《GetAscendQuantTmpBufferFactorSize》说明获取AscendQuant接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。。二者在AscendQuant的Host侧workspace上界/下界必须与该量化Kernel及factor查询匹配上存在可执行的直接衔接。
<!-- cannbot:related:end -->
