---
type: API
title: SetGradOutputShape
description: 设置GradOutput的形状：Batch、Channel、Depth、Height、Width。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetGradOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGradOutputShape

设置GradOutput的形状：Batch、Channel、Depth、Height、Width。

函数原型：void SetGradOutputShape(int64_t n, int64_t c, int64_t d, int64_t h, int64_t w)

参数：
- n：输入输入GradOutput的Batch值。
- c：输入输入GradOutput的Channel值。
- d：输入输入GradOutput的Depth值。
- h：输入输入GradOutput的Height值。
- w：输入输入GradOutput的Width值。

<!-- cannbot:related:start -->
## 相关

- [SetGradOutputShape](../conv3_d_backprop_input_tiling/set_grad_output_shape.md)（`related`）：输入梯度与滤波器梯度 tiling 都用同一五维 GradOutput 形状契约；对照可避免在两类反向算子间混用字段次序。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：使用说明给出 SetGradOutputShape 在完整参数配置序列中的位置，并说明其结果如何进入 GetTiling。
- [SetGradOutput](../conv3_d_backprop_filter_kernel/set_grad_output.md)（`same_topic`）：Host tiling 先声明 GradOutput 的 NCDHW 形状，Kernel SetGradOutput 才能按同一张量契约解释 GM 地址。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《SetGradOutputShape》的实质衔接是：该 setter 把 GradOutput 的 GM/NDC1HWC0 与 FP16/BF16 类型写入 BackpropFilter Host tiling；形状 setter 补齐同一张量描述，GetTiling 生成结构后由 kernel Init/SetGradOutput 按同一契约消费。
<!-- cannbot:related:end -->
