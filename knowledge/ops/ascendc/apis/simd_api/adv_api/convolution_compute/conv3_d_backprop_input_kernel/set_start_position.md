---
type: API
title: SetStartPosition
description: 设置单核上GradOutput载入数据的起始位置。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/SetStartPosition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetStartPosition

设置单核上GradOutput载入数据的起始位置。

函数原型：__aicore__ inline void SetStartPosition(uint32_t curDinStartIdx, int32_t curHoStartIdx)

参数：
- curDinStartIdx（输入）：当前核D方向起始位置。
- curHoStartIdx（输入）：当前核H方向起始位置。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetGradOutput](set_grad_output.md)（`related`）：SetStartPosition 定位的正是 GradOutput 在 D/H 方向的载入起点，必须与 SetGradOutput 绑定的 GM 张量共同解释地址。
- [SetSingleShape](set_single_shape.md)（`related`）：单核 M/K/N 计算范围决定起始 D/H 坐标后本核消费的 GradOutput 区域，两者共同定义单核分片边界。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetStartPosition正文说明“设置单核上GradOutput载入数据的起始位置”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
<!-- cannbot:related:end -->
