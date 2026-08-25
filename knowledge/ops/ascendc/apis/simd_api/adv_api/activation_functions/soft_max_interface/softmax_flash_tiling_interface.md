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

- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`related`）：使用说明给出了先估算临时空间、再生成并传递 tiling 结构的完整 Host→Kernel 流程，补足单接口卡缺失的调用顺序。
- [SoftmaxFlash](softmax_flash.md)（`related`）：该 Host 侧 tiling 函数生成的 SoftMaxTiling 正是同名 SoftmaxFlash kernel 的输入；两侧 isUpdate/isReuseSource 配置必须一致。
- [SoftmaxFlashV2 Tiling接口](softmax_flash_v2_tiling_interface.md)（`related`）：V2 tiling 是当前废弃接口的明确迁移落点，且补充了 dataTypeSize2、isBasicBlock、isFlashOutputBrc 等新契约，能直接指导替换。
- [SoftmaxFlashV3 Tiling接口](softmax_flash_v3_tiling_interface.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlash Tiling接口》明确“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlashV2](softmax_flash_v2.md)（`same_topic`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftmaxFlash Tiling接口》提供“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
<!-- cannbot:related:end -->
