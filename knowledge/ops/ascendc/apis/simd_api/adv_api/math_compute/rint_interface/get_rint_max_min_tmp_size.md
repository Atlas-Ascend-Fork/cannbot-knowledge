---
type: API
title: GetRintMaxMinTmpSize
description: 在host侧获取Rint接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/GetRintMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetRintMaxMinTmpSize

host侧Tiling接口，用于获取Rint接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetRintMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Rint接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Hrint](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《GetRintMaxMinTmpSize》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [GetRintTmpBufferFactorSize](get_rint_tmp_buffer_factor_size.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；GetRintTmpBufferFactorSize正文说明“获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
- [Rint](rint.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；Rint正文说明“获取与输入数据最接近的整数，等距时取偶数”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
- [Rint接口](rint_interface.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；Rint接口正文说明“按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
<!-- cannbot:related:end -->
