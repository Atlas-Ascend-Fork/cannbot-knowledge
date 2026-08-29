---
type: API
title: GetTensorC
description: 在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/GetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetTensorC

在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与[Iterate](../conv3_d_backprop_input_kernel/iterate.md)接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。

函数原型：
template <bool sync = true>
__aicore__ inline void GetTensorC(const AscendC::GlobalTensor<DstT>& output, uint8_t enAtomic = 1, bool enSequentialWrite = false)

参数：
- sync：预留参数，用户无需感知。
- output（输入）：将计算结果搬至Global Memory的GM地址。
- enAtomic（输入）：预留参数，用户无需感知。
- enSequentialWrite（输入）：预留参数，用户无需感知。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Iterate（卷积计算）](iterate.md)（`related`）：“Iterate接口必须在初始化接口及输入输出配置接口之后进行调用，完成卷积反向实现”启动块级计算；“在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。”规定结果消费紧随 Iterate，形成计算与搬出闭环。
<!-- cannbot:related:end -->
