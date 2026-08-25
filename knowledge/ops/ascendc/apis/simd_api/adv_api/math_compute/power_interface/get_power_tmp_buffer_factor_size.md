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

- [GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)（`same_topic`）：焦点处理Power 的 workspace factor 推算；GetPowerMaxMinTmpSize正文界定“在host侧获取Power接口所需的最大和最小临时空间大小，根据输入shape自动适配不同Power调用形式”。候选是 Power 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Power接口](power_interface.md)（`same_topic`）：GetPowerTmpBufferFactorSize说明获取Power接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量；对Power接口而言，Power 计算卡定义三类幂运算重载，而两个临时空间查询接口分别支持动态 shape 和固定空间的分块选择。
- [Power（数学计算）](power.md)（`same_topic`）：焦点处理Power 的 workspace factor 推算；Power（数学计算）正文界定“实现按元素做幂运算功能，提供3类接口，处理逻辑如下： ! !”。候选是 Power 计算、接口页和 max/min 查询，直接消费 factor 结果。
<!-- cannbot:related:end -->
