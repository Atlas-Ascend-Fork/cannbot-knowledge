---
type: API
title: GetXorTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Xor接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Xor_interface/GetXorTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetXorTmpBufferFactorSize

获取Xor接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetXorTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Xor](xor.md)（`related`）：固定缓存下，GetXorTmpBufferFactorSize 提供 Xor 的存活节点倍数和额外空间，直接用于反算一次 calCount。
- [GetXorMaxMinTmpSize](get_xor_max_min_tmp_size.md)（`same_topic`）：Both APIs size the same Xor workspace: one returns bounds directly and the other returns factors for formula-based sizing.
- [Xor接口](xor_interface.md)（`same_topic`）：《Xor接口》明确“按元素执行异或（Xor）运算，并提供临时空间大小获取接口。”；它与《GetXorTmpBufferFactorSize》的“获取maxLiveNodeCount和extraBuf，用于推算Xor接口在固定临时空间下单次最大计算元素数量。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
