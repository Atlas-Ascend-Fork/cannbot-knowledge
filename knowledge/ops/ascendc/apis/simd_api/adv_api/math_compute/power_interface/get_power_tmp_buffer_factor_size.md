---
type: API
title: GetPowerTmpBufferFactorSize
description: 获取Power接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Power_interface/GetPowerTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetPowerTmpBufferFactorSize

获取Power接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。

函数原型：void GetPowerTmpBufferFactorSize(const bool baseIsTensor, const bool expIsTensor, const bool typeIsInt, const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：baseIsTensor为底数是否为Tensor；expIsTensor为指数是否为Tensor；typeIsInt为数据类型是否为int；typeSize为数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize。maxLiveNodeCount可能为0，需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)（`related`）：“currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize”解决固定空间下的最大计算量；“在minValue到maxValue范围内，临时空间越大性能越好。”解决固定计算量下的空间范围与性能取舍，两者是 Power tiling 的互补 sizing 路线。
- [Power（数学计算）](power.md)（`related`）：“currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize”从固定 UB 预算反推单次元素数；“临时空间大小通过GetPowerMaxMinTmpSize获取。”说明 Power kernel 的另一种显式临时空间获取入口，两者构成 host 分块与 kernel 调用的选型链。
<!-- cannbot:related:end -->
