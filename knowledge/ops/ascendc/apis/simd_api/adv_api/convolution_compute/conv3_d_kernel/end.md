---
type: API
title: 卷积计算End
description: 在Conv3D计算完成后，必须调用一次End函数，以清除EventID并释放内部申请的临时内存。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 卷积计算End

在Conv3D计算完成后，必须调用一次End函数，以清除EventID并释放内部申请的临时内存。

函数原型：void End()

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《卷积计算End》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D Kernel侧接口](conv3d_kernel.md)（`same_topic`）：卷积计算End 与《Conv3D Kernel侧接口》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [Conv3DUsage](conv3_d_usage.md)（`same_topic`）：卷积计算End 与《Conv3DUsage》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：卷积计算End 与《Conv3D模板参数》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [GetTensorC](../conv3_d_backprop_filter_kernel/get_tensor_c.md)（`same_topic`）：卷积计算End 与《GetTensorC》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [IterateAll](iterate_all.md)（`same_topic`）：卷积计算End 与《IterateAll》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [Iterate（卷积计算）](../conv3_d_backprop_filter_kernel/iterate.md)（`same_topic`）：卷积计算End 与《Iterate（卷积计算）》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算End](../conv3_d_backprop_filter_kernel/end.md)（`same_topic`）：卷积计算End 与《卷积计算End》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算End](../conv3_d_backprop_input_kernel/end.md)（`same_topic`）：卷积计算End 与《卷积计算End》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](../conv3_d_backprop_filter_kernel/init.md)（`same_topic`）：卷积计算End 与《卷积计算Init》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：卷积计算End 与《卷积计算Init》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
<!-- cannbot:related:end -->
