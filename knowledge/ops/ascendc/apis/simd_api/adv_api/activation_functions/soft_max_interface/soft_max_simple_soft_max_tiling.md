---
type: API
title: SoftMax/SimpleSoftMax Tiling
description: 用于获取SoftMax/SimpleSoftMax Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftMax-SimpleSoftMax-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SoftMax/SimpleSoftMax Tiling

用于获取SoftMax/SimpleSoftMax Tiling参数。

函数原型：
void SoftMaxTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxTiling)
void SoftMaxTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, AscendC::tiling::SoftMaxTiling& softmaxTiling)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：参与计算的max和sum的数据类型，比如half=2。
- isReuseSource（输入）：与kernel侧接口配置保持一致。
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：参与计算的max和sum的数据类型，比如half=2。

返回值：GetSoftMaxMaxTmpSize返回SoftMax/SimpleSoftMax接口能完成计算所需最大临时空间大小，单位为Byte。

<!-- cannbot:related:start -->
## 相关

- [ScaledMaskedSoftmax A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/vfusion/scaled_masked_softmax.md)（`related`）：“`SetPaddingInfo/SetUbSplitInfo/SetSoftmaxTiling/SetTilingKey`”；“void SoftMaxTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxTiling)”。算子 Host Tiling 直接调用该高阶 API 生产 SoftMaxTiling POD。
<!-- cannbot:related:end -->
