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

<!-- cannbot:related:start -->
## 相关

- [IsBasicBlockInSoftMax](is_basic_block_in_soft_max.md)（`related`）：IsBasicBlockInSoftMax 根据输入形状判断基本块路径，可用于给 V2 tiling 的 isBasicBlock 赋值并与 Kernel 分支对齐。
- [SoftmaxFlash](softmax_flash.md)（`related`）：迁移到 SoftmaxFlashV2 后必须同步改用 V2 tiling 接口；旧 tiling 结构不能替代 V2 的 Host 配置。
- [SoftmaxFlash Tiling接口](softmax_flash_tiling_interface.md)（`related`）：V2 tiling 是当前废弃接口的明确迁移落点，且补充了 dataTypeSize2、isBasicBlock、isFlashOutputBrc 等新契约，能直接指导替换。
- [SoftmaxFlashV3 Tiling接口](softmax_flash_v3_tiling_interface.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlashV2 Tiling接口》明确“用于获取SoftmaxFlashV2接口所需的Tiling参数。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlashV2](softmax_flash_v2.md)（`same_topic`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftmaxFlashV2 Tiling接口》提供“用于获取SoftmaxFlashV2接口所需的Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
<!-- cannbot:related:end -->
