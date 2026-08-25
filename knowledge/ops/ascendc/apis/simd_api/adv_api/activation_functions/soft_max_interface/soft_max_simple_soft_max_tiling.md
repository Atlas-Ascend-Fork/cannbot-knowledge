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

- [Softmax 手工尾填充会触发 Vector 异常](../../../../../runbooks/compilation/softmax_manual_tail_fill_route_vector_exception.md)（`exemplifies`）：SoftMax/SimpleSoftMax Tiling 接口负责根据真实 shape 生成计算参数，正是解除本卡 banned 手工补齐路线前必须恢复的契约。
- [flash在线softmax JIT重排致精度超阈](../../../../../runbooks/precision/flash_softmax_jit.md)（`exemplifies`）：正式 tiling 页给出 tile/临时空间基线，可与 JIT 模板参数对照。
- [IsBasicBlockInSoftMax](is_basic_block_in_soft_max.md)（`related`）：SoftMaxTilingFunc produces the SoftMaxTiling structure whose basic-block eligibility the focal predicate inspects.
- [SimpleSoftMax](simple_soft_max.md)（`related`）：《SoftMax/SimpleSoftMax Tiling》明确“用于获取SoftMax/SimpleSoftMax Tiling参数。”；它与《SimpleSoftMax》的“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”在实际调用参数、数据流或结果校验上直接衔接。
- [SoftMax](soft_max.md)（`same_topic`）：《SoftMax》的任务是“对输入tensor按行做Softmax计算，内部包含reducemax、exp、reducesum和div过程，可输出sum和max中间结果，支持ND和NZ格式。”。《SoftMax/SimpleSoftMax Tiling》具体提供“用于获取SoftMax/SimpleSoftMax Tiling参数。”，它直接用于SoftMax 的 Tiling、输出规整、跨 VL 规约状态和尾块同步闭环。
- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SoftMax/SimpleSoftMax Tiling》明确提供“用于获取SoftMax/SimpleSoftMax Tiling参数。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
<!-- cannbot:related:end -->
