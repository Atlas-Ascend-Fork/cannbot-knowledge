---
type: API
title: GetFloorTmpBufferFactorSize
description: 获取Floor接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Floor_interface/GetFloorTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetFloorTmpBufferFactorSize

获取Floor接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetFloorTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Floor](floor.md)（`related`）：Floor 的显式 sharedTmpBuffer 重载直接消费 Host 侧预算；FactorSize 用于在 UB 已知时反推可处理规模，最终仍需满足 Floor 的不重叠和输入值域约束。
- [Floor接口](floor_interface.md)（`related`）：固定空间时 factor-size 决定单次可处理元素数。
- [GetFloorMaxMinTmpSize](get_floor_max_min_tmp_size.md)（`same_topic`）：GetFloorMaxMinTmpSize 与《GetFloorTmpBufferFactorSize》的实质衔接是：该 host 查询给 Floor 高阶接口分配最大/最小临时空间，factor 查询再把选定空间换算为 kernel 单次处理量。
<!-- cannbot:related:end -->
