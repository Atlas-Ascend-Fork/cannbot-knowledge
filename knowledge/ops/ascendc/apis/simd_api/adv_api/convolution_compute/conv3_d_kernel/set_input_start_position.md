---
type: API
title: SetInputStartPosition
description: 设置单核上特征矩阵Input载入数据的起始位置。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetInputStartPosition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputStartPosition

设置单核上特征矩阵Input载入数据的起始位置。

函数原型：__aicore__ inline void SetInputStartPosition(int64_t diStartPos, int64_t mStartPos)

参数：
- diStartPos（输入）：单核上Din方向起始位置。
- mStartPos（输入）：单核上M方向起始位置。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetInput](set_input.md)（`related`）：SetInput 绑定整块 feature-map GM，而 SetInputStartPosition 再为当前核指定 Din/M 起点；多核 Conv3D 输入配置需要二者共同完成。
<!-- cannbot:related:end -->
