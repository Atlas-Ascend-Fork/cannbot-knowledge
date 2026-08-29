---
type: API
title: SoftmaxFlashV3 Tiling接口
description: 用于获取SoftmaxFlashV3接口所需的Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV3_Tiling_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV3 Tiling接口

用于获取SoftmaxFlashV3接口所需的Tiling参数。

函数原型：
void GetSoftMaxFlashV3MaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2, uint32_t& maxValue, uint32_t& minValue, const bool isUpdate, const bool isBasicBlock = false)
void SoftMaxFlashV3TilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2,const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxFlashV3Tiling, const bool isUpdate,const bool isBasicBlock = false)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize1（输入）：输入srcTensor的数据类型大小，即对应SoftMaxFlashV3 Kernel函数中模板参数T的数据类型大小。当前模板参数T仅支持half类型，故此参数只支持取值为2。
- dataTypeSize2（输入）：inMeanTensor、inExpSumTensor 和 inMaxTensor 的元素字节数，对应 kernel 模板参数 U；U 当前仅支持 float，因此该参数只能取 4。
- maxValue（输出）：SoftMaxFlashV3接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。
- minValue（输出）：SoftMaxFlashV3接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxFlashV3](softmax_flash_v3.md)（`related`）：对输入tensor x的尾轴进行切分，分块个数为splitMeanCnt；用于获取SoftmaxFlashV3接口所需的Tiling参数。右卡在 Host 侧按 srcShape、dtype 与 update/basic-block 配置生成临时空间和 Tiling 参数，左卡在 Device 侧消费这些配置执行 PASA 分块计算；两端是参数生产到 Kernel 消费的互补任务链。
<!-- cannbot:related:end -->
