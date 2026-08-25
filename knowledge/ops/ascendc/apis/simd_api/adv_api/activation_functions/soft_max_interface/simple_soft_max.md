---
type: API
title: SimpleSoftMax
description: 使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SimpleSoftMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SimpleSoftMax

将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m,n]按行做如下计算，与SoftMax接口不同，该接口内部没有reduce过程计算sum和max数据，而是使用计算好的sum和max数据对输入tensor做Softmax计算。计算公式如下：

函数原型：template <typename T, bool isReuseSource = false, bool isBasicBlock = false, bool isDataFormatNZ = false, const SoftmaxConfig& config = SOFTMAX_DEFAULT_CFG>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：该参数预留，传入默认值false即可。
- isBasicBlock：srcTensor和dstTensor的shape信息和Tiling切分策略满足基本块要求的情况下，可以设置为true开启该参数用于提升性能，默认为false表示不开启。是否满足基本块的要求，可以采用如下两种方式之一判断：srcTensor和dstTensor的shape信息[m,n]需要满足如下条件：尾轴长度n小于2048并且大于等于256/sizeof(T)（即half场景下n最小为128，float场景下n最小为64），同时n是64的倍数；非尾轴长度的乘积m为8的倍数。

约束：
- srcTensor和dstTensor的Tensor空间可以复用。
- inSumTensor和inMaxTensor为输入，并且last轴长度必须固定32Byte。
- inSumTensor和inMaxTensor的数据类型需要保持一致。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [IsBasicBlockInSoftMax](is_basic_block_in_soft_max.md)（`related`）：《IsBasicBlockInSoftMax》明确“用于判断SoftMaxTiling结构是否符合基本块特征。”；它与《SimpleSoftMax》的“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”在实际调用参数、数据流或结果校验上直接衔接。
- [SoftMax/SimpleSoftMax Tiling](soft_max_simple_soft_max_tiling.md)（`related`）：《SoftMax/SimpleSoftMax Tiling》明确“用于获取SoftMax/SimpleSoftMax Tiling参数。”；它与《SimpleSoftMax》的“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”在实际调用参数、数据流或结果校验上直接衔接。
- [SoftMax](soft_max.md)（`same_topic`）：《SoftMax》的任务是“对输入tensor按行做Softmax计算，内部包含reducemax、exp、reducesum和div过程，可输出sum和max中间结果，支持ND和NZ格式。”。《SimpleSoftMax》具体提供“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”，它直接用于SoftMax 的 Tiling、输出规整、跨 VL 规约状态和尾块同步闭环。
- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SimpleSoftMax》明确提供“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
<!-- cannbot:related:end -->
