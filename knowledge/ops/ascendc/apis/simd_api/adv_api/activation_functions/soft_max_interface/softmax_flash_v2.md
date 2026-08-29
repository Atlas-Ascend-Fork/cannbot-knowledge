---
type: API
title: SoftmaxFlashV2
description: SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV2

SoftmaxFlash增强版本，对应FlashAttention-2算法。将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m,n]按行做如下计算，不同的update值对应不同的计算公式，其中x、inmax和insum为输入，M、S、E均为输出。 update 为 false 与 true 时采用不同公式，具体输入输出关系见固定来源。

函数原型：template <typename T, bool isUpdate = false, bool isReuseSource = false, bool isBasicBlock = false, bool isDataFormatNZ = false, const SoftmaxConfig& config = SOFTMAX_DEFAULT_CFG>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isUpdate：是否开启update部分中的计算。
- isReuseSource：该参数预留，传入默认值false即可。
约束：
- srcTensor和dstTensor的Tensor的空间可以复用，maxTensor和inMaxTensor的空间可以复用，expSumTensor和inExpSumTensor的空间可以复用。
- 除 SoftmaxMode::SOFTMAX_OUTPUT_WITHOUT_BRC 非拓展模式外，expSumTensor、maxTensor、expMaxTensor、inExpSumTensor 和 inMaxTensor 的 last 轴长度必须固定为 32 Byte。
- 对于输出ReduceMax的接口：

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxFlashV2 Tiling接口](softmax_flash_v2_tiling_interface.md)（`same_topic`）：SoftmaxFlash增强版本，对应FlashAttention-2算法。；用于获取SoftmaxFlashV2接口所需的Tiling参数。。kernel API 定义 SoftmaxFlashV2 计算，Tiling API 专门为该计算生成切分参数；实现时必须让 isUpdate 与 isBasicBlock 等配置在两侧一致。
<!-- cannbot:related:end -->
