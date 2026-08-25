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

- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`related`）：Conv3DBackpropFilter使用说明 与《GetTensorC》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate 先把一个 baseM×baseN 梯度块写入 L0C，GetTensorC 随后把同一结果块搬到 GM，两者是不可拆分的计算—取回协议。
- [卷积计算Init](init.md)（`related`）：卷积计算Init 与《GetTensorC》的实质衔接是：Init 消费同一 Conv3DBackpropFilter tiling 并建立资源状态，随后由输入、梯度、起始位置、单 shape、Iterate、取结果和 End 完成一轮对象生命周期。
- [SetInput](set_input.md)（`same_topic`）：SetInput 与《GetTensorC》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《GetTensorC》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《GetTensorC》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [卷积计算End](../conv3_d_kernel/end.md)（`same_topic`）：卷积计算End 与《GetTensorC》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
<!-- cannbot:related:end -->
