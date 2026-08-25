---
type: API
title: SoftmaxFlashV3
description: SoftmaxFlash增强版本，对应Softmax PASA算法。对输入tensor尾轴切分并按update模式计算softmax的均值、最大值和指数和，仅支持ND格式输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV3.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV3

SoftmaxFlash增强版本，对应Softmax PASA算法。将输入tensor[m0, m1, ..., mt, n]（t大于或等于0）的非尾轴长度m0, m1, ..., mt相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor x的尾轴进行切分，分块个数为splitMeanCnt，切分后的tensor为x_cnti。按如下公式进行计算，其中x、inmax、insum、inmean为输入，M、S、E、A均为输出。

函数原型：template <typename T, typename U, bool isUpdate = false, bool isReuseSource = false, bool isBasicBlock = false, bool isDataFormatNZ = false, const SoftmaxConfig& config = SOFTMAX_DEFAULT_CFG>

参数：
- T：输入srcTensor及输出dstTensor、expMaxTensor操作数的数据类型。支持的数据类型为：half。
- U：输入inMeanTensor、inExpSumTensor、inMaxTensor及输出meanTensor、expSumTensor、maxTensor操作数的数据类型。支持的数据类型为：float。
- isUpdate：是否开启update为true的计算。
约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 对于输入srcTensor需要满足：尾轴长度n大于等于512，同时n是64的倍数；非尾轴长度的乘积m为8的倍数。
- srcTensor和dstTensor的Tensor的空间可以复用，meanTensor和inMeanTensor的空间可以复用，maxTensor和inMaxTensor的空间可以复用，expSumTensor和inExpSumTensor的空间可以复用。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。
