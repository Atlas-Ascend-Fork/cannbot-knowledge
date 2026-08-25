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

- [算子实现](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md)（`explains`）：算子实现 与《Iterate（卷积计算）》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [GetTensorC](get_tensor_c.md)（`related`）：Iterate 先把一个 baseM×baseN 梯度块写入 L0C，GetTensorC 随后把同一结果块搬到 GM，两者是不可拆分的计算—取回协议。
- [SetInput](set_input.md)（`related`）：SetInput 与《Iterate（卷积计算）》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel.md)（`same_topic`）：Iterate（卷积计算） 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`same_topic`）：Iterate（卷积计算） 与《Conv3DBackpropFilter使用说明》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetGradOutput](set_grad_output.md)（`same_topic`）：Iterate（卷积计算） 与《SetGradOutput》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《Iterate（卷积计算）》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [SetStartPosition](set_start_position.md)（`same_topic`）：Iterate（卷积计算） 与《SetStartPosition》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [卷积计算End](end.md)（`same_topic`）：Iterate（卷积计算） 与《卷积计算End》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [卷积计算End](../conv3_d_kernel/end.md)（`same_topic`）：卷积计算End 与《Iterate（卷积计算）》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：Iterate（卷积计算） 与《卷积计算Init》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
<!-- cannbot:related:end -->
