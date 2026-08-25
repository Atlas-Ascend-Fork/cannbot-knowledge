---
type: API
title: SetSingleShape
description: 设置Conv3DBackpropInput在单核上计算的形状，单位为元素个数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleShape

设置Conv3DBackpropInput在单核上计算的形状，单位为元素个数。

函数原型：__aicore__ inline void SetSingleShape(uint64_t singleShapeM, uint64_t singleShapeK, uint32_t singleShapeN)

参数：
- singleShapeM（输入）：单核上M的大小，单位为元素。
- singleShapeK（输入）：单核上K的大小，单位为元素。
- singleShapeN（输入）：单核上N的大小，单位为元素。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Iterate（卷积计算）](iterate.md)（`related`）：SetSingleShape 决定单核单轮 Iterate 维护的计算范围和尾块。
- [SetStartPosition](set_start_position.md)（`related`）：单核 M/K/N 计算范围决定起始 D/H 坐标后本核消费的 GradOutput 区域，两者共同定义单核分片边界。
- [卷积计算Init](init.md)（`related`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《卷积计算Init》补充：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《Conv3DBackpropInput》补充：提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。
- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel.md)（`same_topic`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《Conv3DBackpropInput Kernel侧接口》补充：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
- [GetSingleShape](../../cube_compute/matmul_tiling/get_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
<!-- cannbot:related:end -->
