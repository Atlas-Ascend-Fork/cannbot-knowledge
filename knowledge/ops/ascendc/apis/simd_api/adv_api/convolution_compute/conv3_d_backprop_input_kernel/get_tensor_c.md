---
type: API
title: GetTensorC
description: 在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/GetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetTensorC

在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与[Iterate](iterate.md)接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。

函数原型：
template <bool sync = true>
__aicore__ inline void GetTensorC(const AscendC::GlobalTensor<DstT>& output, uint8_t enAtomic = 0, bool enSequentialWrite = false)

参数：
- sync：预留参数，用户无需感知。
- output（输入）：将计算结果搬至Global Memory的GM地址。
- enAtomic（输入）：预留参数，用户无需感知。
- enSequentialWrite（输入）：预留参数，用户无需感知。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel.md)（`related`）：GetTensorC说明在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵；对Conv3DBackpropInput Kernel侧接口而言，Host 侧生成的 TConv3DBackpropInputTiling 直接喂给 Kernel Init；Kernel 完成 Iterate 后必须用 GetTensorC 将 L0C 结果搬回 GM。
- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate（卷积计算）说明每次调用Iterate时，会计算出一个baseM \ baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C Buffer中的数据将被写入目标地址。
- [卷积计算End](end.md)（`related`）：GetTensorC 取出计算结果，随后 End 释放内部资源，二者规定结果消费与销毁顺序。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；GetTensorC正文说明“在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
<!-- cannbot:related:end -->
