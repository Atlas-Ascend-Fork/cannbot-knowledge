---
type: API
title: SetSingleShape
description: 设置Conv3DBackpropFilter在单核上计算的形状。用于运行时修改shape。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleShape

设置Conv3DBackpropFilter在单核上计算的形状。用于运行时修改shape。

函数原型：__aicore__ inline void SetSingleShape(uint64_t singleCoreM, uint64_t singleCoreN, uint64_t singleCoreK)

参数：
- singleCoreM（输入）：单核上M的大小，单位为元素个数。
- singleCoreN（输入）：单核上N的大小，单位为元素个数。
- singleCoreK（输入）：单核上K的大小，单位为元素个数。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetInput](set_input.md)（`related`）：SetInput 与《SetSingleShape》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel.md)（`same_topic`）：SetSingleShape 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`same_topic`）：SetSingleShape 与《Conv3DBackpropFilter使用说明》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [GetSingleShape](../../cube_compute/matmul_tiling/get_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：SetSingleShape 与《GetTensorC》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：SetSingleShape 与《Iterate（卷积计算）》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [SetGradOutput](set_grad_output.md)（`same_topic`）：SetSingleShape 与《SetGradOutput》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [SetStartPosition](set_start_position.md)（`same_topic`）：SetSingleShape 与《SetStartPosition》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [卷积计算End](end.md)（`same_topic`）：SetSingleShape 与《卷积计算End》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [卷积计算Init](init.md)（`same_topic`）：SetSingleShape 与《卷积计算Init》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
<!-- cannbot:related:end -->
