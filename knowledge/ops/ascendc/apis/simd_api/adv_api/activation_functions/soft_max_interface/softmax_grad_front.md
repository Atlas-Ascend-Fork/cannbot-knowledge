---
type: API
title: SoftmaxGradFront
description: 对输入tensor按行做softmax梯度前向计算，计算grad与src乘积的按行求和结果并按datablock广播输出，支持ND和NZ格式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxGradFront.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SoftmaxGradFront

将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m,n]按行做gradfront反向计算，计算公式如下： 当输入shape为ND格式时，内部的reduce过程按last轴进行；当输入shape为NZ格式时，内部的reduce过程按照last轴和first轴进行，，reduce过程可以参考SoftMax中的图示说明。

函数原型：template <typename T, bool isBasicBlock = false, bool isDataFormatNZ = false>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isBasicBlock：srcTensor和gradTensor的shape信息和Tiling切分策略满足基本块要求的情况下，可以设置为true开启该参数用于提升性能，默认为false表示不开启。是否满足基本块的要求，，可以采用如下两种方式之一判断：srcTensor和dstTensor的shape信息[m,n]需要满足如下条件：尾轴长度n小于2048并且大于等于256/sizeof(T)（即half场景下n最小为128，float场景下n最小为64），同时n是64的倍数；非尾轴长度的乘积m为8的倍数。
- isDataFormatNZ：当前输入输出的数据格式是否为NZ格式，默认数据格式为ND，即默认取值为false。
约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 当参数softmaxShapeInfo中srcM != oriSrcM或者srcK != oriSrcK时，开发者需要对GM上的原始输入(oriSrcM, oriSrcK\)在M或K方向补齐数据到\(srcM, srcK\)，补齐的数据会参与部分运算，在输入输出复用的场景下，API的计算结果会覆盖srcTensor中补齐的原始数据，在输入输出不复用的场景下，API的计算结果会覆盖dstTensor中对应srcTensor补齐位置的数据。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxGrad Tiling接口](softmax_grad_tiling_interface.md)（`same_topic`）：将输入tensor［m0, m1, ...mt, n］（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作［m, n］。对输入tensor［m,n］按行做gradfront反向计算，计算公式如下： 当输入shape为ND格式时，内部的reduce过程按last轴进行；当输入shape为NZ格式时，内部的reduce过程按照last轴和first轴进行，，reduce过程可以参考SoftMax中的图示说明。；- isFront（输入）：是否只计算，和kernel侧的SoftmaxGrad接口一致，默认false。。SoftmaxGradFront 是 kernel 侧的前段梯度计算变体，Tiling 接口用 isFront 参数选择与该变体一致的切分契约。
<!-- cannbot:related:end -->
