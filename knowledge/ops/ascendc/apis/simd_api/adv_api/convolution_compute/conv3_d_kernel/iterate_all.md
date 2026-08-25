---
type: API
title: IterateAll
description: 通过设置Output在GM上的首地址，一次性计算单核卷积输出数据块并写入结果矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/IterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# IterateAll

通过设置结果矩阵Output在GM上的首地址，本接口一次性计算singleCo * singleDo * singleM大小的数据块，并写到结果矩阵Output中。 本接口提供单核内卷积计算能力，singleCo为多核切分后单个核内的输出通道大小；singleDo为多核切分后单个核内的Dout大小；singleM为多核切分后单个核内的M大小。singleCo、singleDo和singleM的大小通过SetSingleOutputShape接口设置。

函数原型：__aicore__ inline void IterateAll(const AscendC::GlobalTensor<OutputT>& output, bool enPartialSum = false)

参数：
- output（输入）：Output在GM上的地址。类型为GlobalTensor。结果矩阵Output支持的数据类型为：half、bfloat16_t。
- enPartialSum（输入）：预留参数。

约束：
- IterateAll 仅支持单 batch；多 batch 场景需逐 batch 调用 SetInput、IterateAll 和 End。
- IterateAll接口必须在初始化接口及输入输出配置接口之后进行调用，完成Conv3D计算，调用顺序如下。 ... 输入输出配置 IterateAll(...);

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
