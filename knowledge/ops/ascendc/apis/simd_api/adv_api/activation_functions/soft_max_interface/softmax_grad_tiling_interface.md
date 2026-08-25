---
type: API
title: SoftmaxGrad Tiling接口
description: 用于获取SoftmaxGrad Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxGrad_Tiling_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SoftmaxGrad Tiling接口

用于获取SoftmaxGrad Tiling参数。

函数原型：
void SoftMaxGradTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxGradTiling, const bool isFront = false)
void SoftMaxGradTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, AscendC::tiling::SoftMaxTiling& softmaxGradTiling, const bool isFront = false)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：计算的数据类型，比如half=2。
- isFront（输入）：是否只计算，和kernel侧的SoftmaxGrad接口一致，默认false。
- isReuseSource（输入）：与kernel侧接口配置保持一致。
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。

返回值：GetSoftMaxGradMinTmpSize返回SoftmaxGrad接口能完成计算所需最小临时空间大小，单位为Byte。

<!-- cannbot:related:start -->
## 相关

- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`same_topic`）：SoftmaxGrad Tiling接口 与《SoftMax Tiling使用说明》的实质衔接是：SoftmaxGrad tiling 直接驱动反向 kernel，并与 forward/adjust/basic-block、rank 校验和 tiling 默认项配套。
- [SoftmaxGrad](softmax_grad.md)（`same_topic`）：SoftmaxGrad Tiling接口 与《SoftmaxGrad》的实质衔接是：SoftmaxGrad tiling 直接驱动反向 kernel，并与 forward/adjust/basic-block、rank 校验和 tiling 默认项配套。
- [SoftmaxGradFront](softmax_grad_front.md)（`same_topic`）：SoftmaxGrad Tiling接口 与《SoftmaxGradFront》的实质衔接是：SoftmaxGrad tiling 直接驱动反向 kernel，并与 forward/adjust/basic-block、rank 校验和 tiling 默认项配套。
<!-- cannbot:related:end -->
