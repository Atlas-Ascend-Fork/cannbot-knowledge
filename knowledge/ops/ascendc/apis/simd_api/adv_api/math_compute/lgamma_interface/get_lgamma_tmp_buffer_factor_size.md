---
type: API
title: GetLgammaTmpBufferFactorSize
description: 获取Lgamma接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/GetLgammaTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLgammaTmpBufferFactorSize

获取Lgamma接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。

函数原型：void GetLgammaTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Lgamma](lgamma.md)（`related`）：factor 查询产生的临时空间容量用于决定 Lgamma kernel 单次可处理元素量，执行接口直接消费该 Tiling 决策。
- [Lgamma接口](lgamma_interface.md)（`related`）：因子查询把固定 workspace 换算成 Lgamma 单次最大处理元素数，补足分块 tiling 决策。
- [GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)（`same_topic`）：Lgamma factor 查询用 maxLiveNodeCount/extraBuf 反推固定空间下的处理量，MaxMin 查询则给出同一 Lgamma 接口的可预留空间上下界，两者共同闭合 Tiling 预算。
<!-- cannbot:related:end -->
