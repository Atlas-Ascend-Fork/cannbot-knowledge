---
type: API
title: GetBroadCastMaxMinTmpSize
description: 在host侧获取Broadcast接口计算所需的最大和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/GetBroadCastMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetBroadCastMaxMinTmpSize

host侧Tiling接口，用于获取Broadcast接口所需的最大和最小临时空间大小。

函数原型：void GetBroadCastMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。在minValue到maxValue范围内临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Broadcast（张量变换）](broadcast.md)（`related`）：临时空间大小通过GetBroadCastMaxMinTmpSize获取。；host侧Tiling接口，用于获取Broadcast接口所需的最大和最小临时空间大小。。Broadcast 直接指定右侧接口为其临时空间来源，右侧为计算接口返回可选范围；两者分别承担 Kernel 计算与 Host 资源查询，是明确的前后任务链。
<!-- cannbot:related:end -->
