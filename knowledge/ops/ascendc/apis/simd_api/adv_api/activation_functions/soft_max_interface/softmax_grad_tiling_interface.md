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

- [SoftmaxGradFront](softmax_grad_front.md)（`same_topic`）：将输入tensor［m0, m1, ...mt, n］（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作［m, n］。对输入tensor［m,n］按行做gradfront反向计算，计算公式如下： 当输入shape为ND格式时，内部的reduce过程按last轴进行；当输入shape为NZ格式时，内部的reduce过程按照last轴和first轴进行，，reduce过程可以参考SoftMax中的图示说明。；- isFront（输入）：是否只计算，和kernel侧的SoftmaxGrad接口一致，默认false。。SoftmaxGradFront 是 kernel 侧的前段梯度计算变体，Tiling 接口用 isFront 参数选择与该变体一致的切分契约。
<!-- cannbot:related:end -->
