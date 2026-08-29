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

- [Floor](floor.md)（`related`）：“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetFloorMaxMinTmpSize获取。”明确 Floor 的依赖，而“host侧Tiling接口，用于获取Floor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”定义 Host 侧生产值；二者构成 sharedTmpBuffer 从 Host 计算到 Kernel 调用的直接合同。
- [Floor接口](floor_interface.md)（`related`）：按元素向负无穷取整，并提供临时空间大小获取接口。；host侧Tiling接口，用于获取Floor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。接口组明确需要临时空间查询，而目标卡给出 Host 侧最大/最小值获取契约，二者共同闭合 Floor 的 Tiling 到 Kernel 使用链。
<!-- cannbot:related:end -->
