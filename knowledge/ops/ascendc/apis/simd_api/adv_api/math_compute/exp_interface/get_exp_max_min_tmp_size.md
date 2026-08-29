---
type: API
title: GetExpMaxMinTmpSize
description: 在host侧获取Exp接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/GetExpMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetExpMaxMinTmpSize

host侧Tiling接口，用于获取Exp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：bool GetExpMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Exp接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

返回值：返回true/false，表明是否能正常获取所需最大最小临时空间。在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Exp](exp.md)（`related`）：“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetExpMaxMinTmpSize获取。”与“host侧Tiling接口，用于获取Exp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”。Exp 的 sharedTmpBuffer 重载需要空间预算，Host 接口给出可用最大值与不得低于的最小值。
- [Exp接口](exp_interface.md)（`related`）：临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。；host侧Tiling接口，用于获取Exp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。前者规定 Exp kernel 的临时空间获取方式，后者正是为 Exp 计算该最大最小空间并生成 Tiling 选择依据的 Host 接口，形成调用前的容量规划链。
<!-- cannbot:related:end -->
