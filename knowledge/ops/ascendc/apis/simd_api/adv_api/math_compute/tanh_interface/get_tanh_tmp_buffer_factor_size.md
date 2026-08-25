---
type: API
title: GetTanhTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Tanh接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tanh_interface/GetTanhTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTanhTmpBufferFactorSize

获取Tanh接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetTanhTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetAtanhTmpBufferFactorSize](../atanh_interface/get_atanh_tmp_buffer_factor_size.md)（`related`）：Atanh 是反函数且容量公式不同。
- [Tanh](tanh.md)（`related`）：GetTanhTmpBufferFactorSize 提供 Tanh 的存活节点倍数和额外空间，供已有 UB 容量反算 calCount，直接决定 Tanh 分块。
- [GetTanhMaxMinTmpSize](get_tanh_max_min_tmp_size.md)（`same_topic`）：MaxMin 按问题规模求空间范围，FactorSize 按现有 UB 反推 Tanh 处理规模；二者共同完成同一 Tanh 临时空间规划。
- [Tanh接口](tanh_interface.md)（`same_topic`）：总页定义 Tanh、workspace 和 factor-size 的完整流程。
<!-- cannbot:related:end -->
