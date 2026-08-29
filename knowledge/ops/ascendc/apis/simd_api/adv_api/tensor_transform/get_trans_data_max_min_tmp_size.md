---
type: API
title: GetTransDataMaxMinTmpSize
description: 在host侧获取TransData接口计算所需的最大和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/GetTransDataMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetTransDataMaxMinTmpSize

host侧Tiling接口，用于获取TransData接口所需的最大和最小临时空间大小。

函数原型：void GetTransDataMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。在minValue到maxValue范围内临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [TransData](trans_data.md)（`related`）：host侧Tiling接口，用于获取TransData接口所需的最大和最小临时空间大小。；提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetTransDataMaxMinTmpSize获取。。Host 接口产出的临时空间区间直接满足 TransData 两种重载的 sharedTmpBuffer 预算契约。
<!-- cannbot:related:end -->
