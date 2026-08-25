---
type: API
title: SoftmaxGrad
description: 对输入tensor按行做softmax梯度反向计算，支持ND和NZ格式，通过isFront参数控制是否仅计算前向求和结果。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxGrad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxGrad

将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m,n]按行做grad反向计算，计算公式如下： 当输入shape为ND格式时，内部的reduce过程按last轴进行；当输入shape为NZ格式时，内部的reduce过程按照last轴和first轴进行，reduce过程可以参考SoftMax中的图示说明。 为方便理解，通过Python脚本实现的方式，表达其计算公式如下，其中src、grad、isFront是源操作数（输入），dst为目的操作数（输出）。

函数原型：
template <typename T, bool isReuseSource = false, bool isDataFormatNZ = false>
__aicore__ inline void SoftmaxGrad(const LocalTensor<T>& dstTensor, const LocalTensor<T>& gradTensor, const LocalTensor<T>& srcTensor, const SoftMaxTiling& tiling, bool isFront = false, const SoftMaxShapeInfo& softmaxShapeInfo = {})

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：该参数预留，传入默认值false即可。
- isDataFormatNZ：当前输入输出的数据格式是否为NZ格式，默认数据格式为ND，即默认取值为false。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 last轴长度需要32Byte对齐，dstTensor的shape与gradTensor，srcTensor的shape一致。
- gradTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 last轴长度需要32Byte对齐，gradTensor的shape与dstTensor，srcTensor的shape一致。

约束：
- srcTensor和dstTensor的Tensor空间可以复用。
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 当参数softmaxShapeInfo中srcM != oriSrcM或者srcK != oriSrcK时，开发者需要对GM上的原始输入(oriSrcM, oriSrcK)在M或K方向补齐数据到(srcM, srcK)，补齐的数据会参与部分运算，在输入输出复用的场景下，API的计算结果会覆盖srcTensor中补齐的原始数据，在输入输出不复用的场景下，API的计算结果会覆盖dstTensor中对应srcTensor补齐位置的数据。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SoftmaxGrad Tiling接口](softmax_grad_tiling_interface.md)（`same_topic`）：SoftmaxGrad Tiling接口 与《SoftmaxGrad》的实质衔接是：SoftmaxGrad tiling 直接驱动反向 kernel，并与 forward/adjust/basic-block、rank 校验和 tiling 默认项配套。
- [SoftmaxGradFront](softmax_grad_front.md)（`same_topic`）：SoftmaxGrad 的 isFront=true 只计算前半结果，正对应 SoftmaxGradFront 单独暴露的前半计算；两者是同一梯度核心对象的整接口与前半接口。
<!-- cannbot:related:end -->
