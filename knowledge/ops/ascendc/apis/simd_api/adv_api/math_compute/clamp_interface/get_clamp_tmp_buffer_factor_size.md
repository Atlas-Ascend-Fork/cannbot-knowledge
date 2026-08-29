---
type: API
title: GetClampTmpBufferFactorSize
description: 获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/GetClampTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetClampTmpBufferFactorSize

获取ClampMax/ClampMin/Clamp接口的maxLiveNodeCount和extraBuf，用于在固定临时空间大小下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetClampTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。

推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”。焦点接口从 shape 求可用空间范围，factor 接口反向从固定缓冲求单次处理元素数，二者共同完成 Clamp workspace 与 tile 大小设计。
- [Clamp（数学计算）](clamp.md)（`same_topic`）：“获取ClampMax/ClampMin/Clamp接口的maxLiveNodeCount和extraBuf，用于在固定临时空间大小下推算算子单次最大计算元素数量。”与“将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。”分别给出双端正文事实；临时空间因子接口专门为 Clamp 计算反推单次元素规模，Clamp 卡定义被切分执行的逐元素上下界语义，二者是同一高阶 API 的容量计算与 Kernel 合同。
<!-- cannbot:related:end -->
