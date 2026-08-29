---
type: API
title: Iterate（卷积计算）
description: 每次调用Iterate时，会计算出一个baseM \ baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C
  Buffer中的数据将被写入目标地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Iterate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Iterate（卷积计算）

每次调用Iterate时，会计算出一个baseM * baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C Buffer中的数据将被写入目标地址。

函数原型：
template <bool sync = true>
__aicore__ inline bool Iterate(bool enPartialSum = false)

参数：
- sync：预留参数，用户无需感知。
- enPartialSum（输入）：预留参数，用户无需感知。

返回值：false：设置的SingleShape上的所有数据已经算完。

约束：
- Iterate接口必须在初始化接口及输入输出配置接口之后进行调用，完成卷积反向实现，调用顺序如下。 ... 输入输出配置 while (Iterate()) { GetTensorC();
- 在多轮循环计算的场景中，在单次循环里计算单核SetSingleShape设置的数据大小。每次单核计算完成后，必须将Conv3DBackpropFilter对象的ctx.isFirstIter_设置为true，以确保下一轮循环中的单核计算能够正确进行。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetTensorC](get_tensor_c.md)（`related`）：“Iterate接口必须在初始化接口及输入输出配置接口之后进行调用，完成卷积反向实现”启动块级计算；“在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。”规定结果消费紧随 Iterate，形成计算与搬出闭环。
- [卷积计算Init](init.md)（`related`）：“Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分”建立对象和资源；“Iterate接口必须在初始化接口及输入输出配置接口之后进行调用，完成卷积反向实现”明确计算阶段依赖初始化，形成同一调用序列。
<!-- cannbot:related:end -->
