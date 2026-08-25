---
type: API
title: SetGradOutputShape
description: 设置GradOutput的形状：Batch、Channel、Depth、Height、Width。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetGradOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGradOutputShape

设置GradOutput的形状：Batch、Channel、Depth、Height、Width。

参数：
- n：输入输入GradOutput的Batch值。
- c：输入输入GradOutput的Channel值。
- d：输入输入GradOutput的Depth值。
- h：输入输入GradOutput的Height值。
- w：输入输入GradOutput的Width值。

返回值：true表示设置成功，false表示设置失败。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetGradOutputShape 等 setter 的结果最终由 GetTiling 汇总生成 Kernel 参数；缺少该调用配置不会形成可用 tiling。
- [SetGradOutput](../conv3_d_backprop_input_kernel/set_grad_output.md)（`related`）：Host 侧设置的 GradOutput 形状必须与 Kernel 侧绑定的实际 GradOutput 张量一致，连接 tiling 配置和计算输入。
- [SetGradOutputShape](../conv3_d_backprop_filter_tiling/set_grad_output_shape.md)（`related`）：输入梯度与滤波器梯度 tiling 都用同一五维 GradOutput 形状契约；对照可避免在两类反向算子间混用字段次序。
- [SetInputShape](set_input_shape.md)（`related`）：SetInputShape 给出待求梯度 Input 的 N/C/D/H/W，SetGradOutputShape 给出反向输入卷积的上游梯度几何；两者的 batch/channel 对应关系和空间尺寸共同约束 tiling。
- [SetStride](set_stride.md)（`related`）：GradOutput shape 与 stride 共同决定反推 Input 的空间范围，是 tiling 合法性校验的关键输入。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《SetGradOutputShape》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《SetGradOutputShape》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
<!-- cannbot:related:end -->
