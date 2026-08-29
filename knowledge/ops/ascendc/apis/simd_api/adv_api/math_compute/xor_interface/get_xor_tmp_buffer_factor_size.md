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

- [GetXorMaxMinTmpSize](get_xor_max_min_tmp_size.md)（`same_topic`）：host侧Tiling接口，用于获取Xor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。获取Xor接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。两端共同定义 Xor 临时空间规划的两个方向：先由 shape 确定可选空间范围，或由既定空间反推单次处理量，Host 可据此检查 Tiling 是否自洽。
<!-- cannbot:related:end -->
