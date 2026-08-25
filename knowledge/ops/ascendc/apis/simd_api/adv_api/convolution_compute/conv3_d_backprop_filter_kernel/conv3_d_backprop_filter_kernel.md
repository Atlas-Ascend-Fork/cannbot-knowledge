---
type: API
title: Conv3DBackpropFilter Kernel侧接口
description: 提供Conv3D反向卷积滤波器梯度的Kernel侧接口，包含Init、SetInput、SetGradOutput、Iterate等方法及使用说明。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Conv3DBackpropFilter_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropFilter Kernel侧接口

提供三维卷积反向滤波器梯度计算的 Kernel 侧接口。
核心方法包括 Init 初始化、SetInput 设置前向输入、SetGradOutput 设置梯度输出、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。
计算过程中通过 Iterate 循环分块处理，最终通过 GetTensorC 获取滤波器梯度结果。

<!-- cannbot:related:start -->
## 相关

- [errcode 82 — streamk stepK 致 L1 越界](../../../../../runbooks/compilation/conv3d_bp_filter_v2_streamk_stepk_l1_overflow_errcode_82.md)（`exemplifies`）：该排障卡定位 Conv3DBackpropFilter stream-k Tiling 在 stepK 调整后遗漏 L1 复核，直接补充本 Kernel 分块运行时报 errcode 82 的根因与验证点。
- [TConv3DBpFilterTiling结构体](../conv3_d_backprop_filter_tiling/t_conv3_d_bp_filter_tiling_struct.md)（`related`）：Conv3DBackpropFilter Kernel 以该 Tiling 结构驱动切分、搬运和计算，是结构体的直接消费者。
- [Conv3DBackpropFilter Tiling侧接口](../conv3_d_backprop_filter_tiling/conv3_d_backprop_filter_tiling.md)（`same_topic`）：Host Tiling 卡计算并序列化 Conv3DBackpropFilter 的分块参数，Kernel 卡按同一 BPF 算子合同解析这些参数并执行反向滤波计算；两者共同构成同一算子的 Host/Device 接口。
- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`same_topic`）：Conv3DBackpropFilter使用说明 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [GetTiling](../conv3_d_backprop_filter_tiling/get_tiling.md)（`same_topic`）：GetTiling 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：Iterate（卷积计算） 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetInput](set_input.md)（`same_topic`）：SetInput 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [卷积计算Init](init.md)（`same_topic`）：卷积计算Init 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：Init 消费同一 Conv3DBackpropFilter tiling 并建立资源状态，随后由输入、梯度、起始位置、单 shape、Iterate、取结果和 End 完成一轮对象生命周期。
<!-- cannbot:related:end -->
