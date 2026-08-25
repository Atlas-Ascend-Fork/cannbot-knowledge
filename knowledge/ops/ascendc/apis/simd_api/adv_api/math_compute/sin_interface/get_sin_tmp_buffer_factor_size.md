---
type: API
title: GetSinTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Sin接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sin_interface/GetSinTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSinTmpBufferFactorSize

获取Sin接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

提供两种重载：一种不带config参数（使用默认SinConfig），另一种带config参数（须与Sin Kernel接口模板参数config保持一致）。函数原型：void GetSinTmpBufferFactorSize([const SinConfig& config,] const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetSinCosTmpBufferFactorSize](../sin_cos_interface/get_sin_cos_tmp_buffer_factor_size.md)（`related`）：同时需要 sin/cos 输出时应使用双输出接口的独立 factor 规则，不能沿用单 Sin 的容量估计。
- [GetSinMaxMinTmpSize](get_sin_max_min_tmp_size.md)（`same_topic`）：MaxMin 给出 Sin 临时空间区间，FactorSize 在固定 buffer 下按 maxLiveNodeCount/extraBuf 反推 count；两者还要求 SinConfig 保持一致。
- [Sin](sin.md)（`same_topic`）：Sin 与《GetSinTmpBufferFactorSize》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [Sin接口](sin_interface.md)（`same_topic`）：Sin 接口总页定义 FactorSize、MaxMinTmpSize 与 Sin 的组合流程。
<!-- cannbot:related:end -->
