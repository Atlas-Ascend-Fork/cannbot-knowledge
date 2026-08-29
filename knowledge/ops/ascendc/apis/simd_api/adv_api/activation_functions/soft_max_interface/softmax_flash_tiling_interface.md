---
type: API
title: SoftmaxFlash Tiling接口
description: 注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlash_Tiling_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SoftmaxFlash Tiling接口

注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。

函数原型：
void SoftMaxFlashTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxFlashTiling, const bool isUpdate = false)
void SoftMaxFlashTilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, AscendC::tiling::SoftMaxTiling& softmaxFlashTiling, const bool isUpdate = false)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：参与计算的maxTensor和sumTensor的数据类型，比如half=2。
- isUpdate（输入）：是否开启刷新功能，和kernel侧SoftmaxFlash接口一致，默认false。
- isReuseSource（输入）：与kernel侧接口配置保持一致。
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。

返回值：GetSoftMaxFlashMaxTmpSize返回SoftmaxFlash接口能完成计算所需最大临时空间大小，单位为Byte。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxFlash](softmax_flash.md)（`related`）：“注意：该接口后续即将废弃，请使用精度和性能更好的SoftmaxFlashV2接口。 Softmax增强版本，除了可以对输入tensor做SoftmaxFlash计算，还可以根据上一次Softmax计算的sum和max来更新本次的Softmax计算结果。”与“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”分别给出两端正文事实；Kernel 侧 SoftmaxFlash 的 update 计算依赖 Host 侧同名 tiling 参数，二者共同构成旧版接口的调用合同与迁移警告。
<!-- cannbot:related:end -->
