---
type: API
title: GetCoshTmpBufferFactorSize
description: 获取Cosh接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cosh_interface/GetCoshTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCoshTmpBufferFactorSize

获取Cosh接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。

函数原型：void GetCoshTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Cosh](cosh.md)（`same_topic`）：GetCoshTmpBufferFactorSize说明获取Cosh接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量；对Cosh而言，Cosh 的 Host Tiling 必须在最大/最小临时空间与 factor 参数之间选择，才能推算 Kernel 单次处理量。
- [Cosh接口](cosh_interface.md)（`same_topic`）：焦点处理Cosh 高阶 API 的计算接口与临时空间计算；GetCoshTmpBufferFactorSize正文说明“获取Cosh接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。候选分别承担 Cosh 实际计算、workspace 上下界和固定空间容量推算。
- [GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)（`same_topic`）：GetCoshMaxMinTmpSize说明在host侧获取Cosh接口预留或申请临时空间的最大和最小值，用于Tiling参数传递。
<!-- cannbot:related:end -->
