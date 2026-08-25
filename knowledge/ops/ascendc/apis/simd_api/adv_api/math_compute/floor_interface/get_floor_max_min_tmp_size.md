---
type: API
title: GetFloorMaxMinTmpSize
description: 在host侧获取Floor接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Floor_interface/GetFloorMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetFloorMaxMinTmpSize

host侧Tiling接口，用于获取Floor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetFloorMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Floor接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Floor接口](floor_interface.md)（`related`）：Floor 调用前用该接口计算 workspace 上下界。
- [Floor](floor.md)（`same_topic`）：GetFloorMaxMinTmpSize 与《Floor》的实质衔接是：该 host 查询给 Floor 高阶接口分配最大/最小临时空间，factor 查询再把选定空间换算为 kernel 单次处理量。
- [GetFloorTmpBufferFactorSize](get_floor_tmp_buffer_factor_size.md)（`same_topic`）：GetFloorMaxMinTmpSize 与《GetFloorTmpBufferFactorSize》的实质衔接是：该 host 查询给 Floor 高阶接口分配最大/最小临时空间，factor 查询再把选定空间换算为 kernel 单次处理量。
<!-- cannbot:related:end -->
