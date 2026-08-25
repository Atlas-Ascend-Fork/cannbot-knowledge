---
type: API
title: IsBasicBlockInSoftMax
description: 用于判断SoftMaxTiling结构是否符合基本块特征。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/IsBasicBlockInSoftMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# IsBasicBlockInSoftMax

用于判断SoftMaxTiling结构是否符合基本块特征。

参数：
- 接口（输入 输出）：功能
- tiling（输入）：待判断的SoftMaxTiling结构，支持optiling::SoftMaxTiling形式入参和AscendC::tiling::SoftMaxTiling形式入参。
- dataTypeSize（输入）：参与计算的srcTensor的数据类型大小，比如half=2。

返回值：- 返回true表示SoftMaxTiling结构满足基本块Tiling特征。

<!-- cannbot:related:start -->
## 相关

- [SimpleSoftMax](simple_soft_max.md)（`related`）：《IsBasicBlockInSoftMax》明确“用于判断SoftMaxTiling结构是否符合基本块特征。”；它与《SimpleSoftMax》的“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”在实际调用参数、数据流或结果校验上直接衔接。
- [SoftMax/SimpleSoftMax Tiling](soft_max_simple_soft_max_tiling.md)（`related`）：SoftMaxTilingFunc produces the SoftMaxTiling structure whose basic-block eligibility the focal predicate inspects.
- [SoftmaxFlashV2 Tiling接口](softmax_flash_v2_tiling_interface.md)（`related`）：IsBasicBlockInSoftMax 根据输入形状判断基本块路径，可用于给 V2 tiling 的 isBasicBlock 赋值并与 Kernel 分支对齐。
- [SoftMax](soft_max.md)（`same_topic`）：《SoftMax》的任务是“对输入tensor按行做Softmax计算，内部包含reducemax、exp、reducesum和div过程，可输出sum和max中间结果，支持ND和NZ格式。”。《IsBasicBlockInSoftMax》具体提供“用于判断SoftMaxTiling结构是否符合基本块特征。”，它直接用于SoftMax 的 Tiling、输出规整、跨 VL 规约状态和尾块同步闭环。
- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《IsBasicBlockInSoftMax》明确提供“用于判断SoftMaxTiling结构是否符合基本块特征。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
<!-- cannbot:related:end -->
