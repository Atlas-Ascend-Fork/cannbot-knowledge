---
type: API
title: SoftmaxFlashV2 Tiling接口
description: 用于获取SoftmaxFlashV2接口所需的Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV2_Tiling_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV2 Tiling接口

用于获取SoftmaxFlashV2接口所需的Tiling参数。

函数原型：
void SoftMaxFlashV2TilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2, const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxFlashTiling, const bool isUpdate, const bool isBasicBlock = false, const bool isFlashOutputBrc = false)
void SoftMaxFlashV2TilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2, const uint32_t localWorkSpaceSize, AscendC::tiling::SoftMaxTiling& softmaxFlashTiling, const bool isUpdate, const bool isBasicBlock = false, const bool isFlashOutputBrc = false)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize1（输入）：计算的源数据的数据类型大小，比如half=2。
- dataTypeSize2（输入）：参与计算的expSumTensor和maxTensor的数据类型大小，比如half=2。
- isUpdate（输入）：是否开启刷新功能，和kernel侧SoftmaxFlashV2接口一致。
- isBasicBlock（输入）：是否开启基本块计算，默认 false，并与 kernel 侧模板参数保持一致；shape 常量化且启用 SoftmaxConfig 时，必须通过 isBasicBlockInSoftmax 获取该值。

返回值：GetSoftMaxFlashV2MinTmpSize返回SoftmaxFlashV2接口能完成计算所需最小临时空间大小，单位为Byte。
