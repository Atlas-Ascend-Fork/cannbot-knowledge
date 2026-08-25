---
type: API
title: 卷积计算End
description: 在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 卷积计算End

在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。

函数原型：__aicore__ inline void End()

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetTensorC](get_tensor_c.md)（`related`）：GetTensorC 取出计算结果，随后 End 释放内部资源，二者规定结果消费与销毁顺序。
- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate 发起反向输入卷积计算，完成后才进入 End 的释放阶段。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；卷积计算End正文说明“在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [卷积计算End](../conv3_d_kernel/end.md)（`same_topic`）：卷积计算End 与《卷积计算End》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：Init 建立 Conv3DBackpropInput 内部状态，End 必须在计算后清理同一对象的 EventID 和临时内存。
<!-- cannbot:related:end -->
