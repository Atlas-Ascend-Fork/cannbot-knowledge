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

- [AscendC Muls cyclic-repeat 致分组 scale 错配](../../../../runbooks/precision/ascendc_muls_cyclic_repeat_scale.md)（`exemplifies`）：AscendC Muls cyclic-repeat 致分组 scale 错配 与《GetBroadCastMaxMinTmpSize》的实质衔接是：Muls 对短 scale 做 cyclic repeat 而分组量化需要 block repeat；Broadcast、Muls、AntiQuant、GroupedMatmul/SwiGLU 案例共同验证 scale 的连续分组映射。
- [Broadcast场景](../../../../guides/operator_practice/simd_operator_impl/vector_programming/broadcast_scenario.md)（`explains`）：Broadcast 需要临时输出空间，Host 侧查询接口为指南中的 UB 预算和 tiling 参数提供边界。
- [Broadcast（张量变换）](broadcast.md)（`related`）：GetBroadCastMaxMinTmpSize 返回的缓存范围专供 Broadcast kernel 使用，shape、typeSize 和 isReuseSource 必须保持一致。
<!-- cannbot:related:end -->
