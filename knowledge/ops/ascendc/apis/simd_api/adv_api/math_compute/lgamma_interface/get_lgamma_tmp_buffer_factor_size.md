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

- [GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)（`related`）：参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。；host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两接口从 shape 到空间上下界和空间到可处理 shape 两个方向闭合 Lgamma 的 Host 临时空间规划。
- [Lgamma](lgamma.md)（`related`）：参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。。因子接口把可用 UB 反推成 Lgamma 可处理 shape，Lgamma 的手工临时空间重载正是该容量规划的消费端。
<!-- cannbot:related:end -->
