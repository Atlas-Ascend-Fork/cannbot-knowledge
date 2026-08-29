---
type: API
title: SoftMax
description: 对输入tensor按行做Softmax计算，内部包含reducemax、exp、reducesum和div过程，可输出sum和max中间结果，支持ND和NZ格式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftMax

将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m, n]按行做如下SoftMax计算： 为方便理解，通过Python脚本实现的方式，表达其计算公式（以输入为ND格式为例）如下，其中src是源操作数（输入），dst、sum、max为目的操作数（输出）。

函数原型：template <typename T, bool isReuseSource = false, bool isBasicBlock = false, bool isDataFormatNZ = false, const SoftmaxConfig& config = SOFTMAX_DEFAULT_CFG>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：该参数预留，传入默认值false即可。
- isBasicBlock：srcTensor和dstTensor的shape信息和Tiling切分策略满足基本块要求的情况下，可以开启该参数用于提升性能，默认不开启。是否满足基本块的要求，可以采用如下两种方式之一判断：srcTensor和dstTensor的shape信息[m,n]需要满足如下条件：尾轴长度n小于2048并且大于等于256/sizeof(T)（即half场景下n最小为128，float场景下n最小为64），同时n是64的倍数；非尾轴长度的乘积m为8的倍数。

约束：
- src和dst的Tensor空间可以复用。
- sumTensor和maxTensor为输出，并且last轴长度必须固定32Byte，非last轴大小需要和src以及dst保持一致。
- sumTensor和maxTensor的数据类型需要保持一致。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [SimpleSoftMax](simple_soft_max.md)（`related`）：- inSumTensor和inMaxTensor为输入，并且last轴长度必须固定32Byte。；- sumTensor和maxTensor为输出，并且last轴长度必须固定32Byte，非last轴大小需要和src以及dst保持一致。；SoftMax 负责计算并输出 sum 与 max，而 SimpleSoftMax 接收已经计算好的 sum 与 max 并省去 reduce，二者构成同一 Softmax 流程中可替换的完整计算与复用中间量路径。
<!-- cannbot:related:end -->
