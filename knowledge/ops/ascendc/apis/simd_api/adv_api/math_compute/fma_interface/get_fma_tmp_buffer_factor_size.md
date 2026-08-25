---
type: API
title: GetFmaTmpBufferFactorSize
description: 获取Fma接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fma_interface/GetFmaTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetFmaTmpBufferFactorSize

获取Fma接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetFmaTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：FMA 一次舍入的精度实例用于验证切分后结果。
- [Fma](fma.md)（`related`）：固定 workspace 下 factor-size 决定单次 Fma tile。
- [Fma接口](fma_interface.md)（`same_topic`）：Fma接口 与《GetFmaTmpBufferFactorSize》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [GetFmaMaxMinTmpSize](get_fma_max_min_tmp_size.md)（`same_topic`）：MaxMin 接口按 shape 正向求 Fma 空间上下界，FactorSize 接口按既有空间反推可处理规模，两者是同一临时空间模型的正反查询。
<!-- cannbot:related:end -->
