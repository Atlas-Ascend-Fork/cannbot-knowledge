---
type: API
title: GetCumSumMaxMinTmpSize
description: 在host侧获取CumSum接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/CumSum_interface/GetCumSumMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCumSumMaxMinTmpSize

host侧Tiling接口，用于获取CumSum接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetCumSumMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isLastAxis, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isLastAxis定义按first轴还是last轴处理（与CumSum接口config.isLastAxis一致）；isReuseSource为是否复用源操作数空间；maxValue输出最大临时空间大小（超出不被使用，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：遵循通用地址对齐约束；输入仅支持二维结构。

<!-- cannbot:related:start -->
## 相关

- [CumSum](cum_sum.md)（`related`）：临时空间大小通过GetCumSumMaxMinTmpSize获取。；host侧Tiling接口，用于获取CumSum接口所需的最大和最小临时空间大小。左卡明确要求由目标接口确定 CumSum 临时空间，右卡又把 isLastAxis 与 Kernel config 对齐并返回 min/max；两端衔接 Host 定容与二维行列累加 Kernel。
<!-- cannbot:related:end -->
