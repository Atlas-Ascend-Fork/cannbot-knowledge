---
type: API
title: SetInput
description: 设置特征矩阵Input。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetInput.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInput

设置特征矩阵Input。

函数原型：__aicore__ inline void SetInput(const AscendC::GlobalTensor<InputT>& input)

参数：
- input（输入）：Input在Global Memory上的首地址。类型为GlobalTensor。特征矩阵Input支持的数据类型为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：SetInput 完成每批输入绑定后，IterateAll 才执行该批完整 Conv3D 计算；多 batch 时明确需要重复 SetInput—IterateAll—End。
- [SetInputStartPosition](set_input_start_position.md)（`related`）：SetInput 绑定整块 feature-map GM，而 SetInputStartPosition 再为当前核指定 Din/M 起点；多核 Conv3D 输入配置需要二者共同完成。
- [SetInputType](../conv3_d_tiling/set_input_type.md)（`related`）：tiling 侧 SetInputType 固定 Input 的 GM 位置、NDC1HWC0 格式和 FP16/BF16 dtype，kernel 侧 SetInput 绑定的张量必须满足该合同。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetInput》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
