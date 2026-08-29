---
type: API
title: GetTensorC
description: 在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/GetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetTensorC

在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与[Iterate](iterate.md)接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。

函数原型：
template <bool sync = true>
__aicore__ inline void GetTensorC(const AscendC::GlobalTensor<DstT>& output, uint8_t enAtomic = 0, bool enSequentialWrite = false)

参数：
- sync：预留参数，用户无需感知。
- output（输入）：将计算结果搬至Global Memory的GM地址。
- enAtomic（输入）：预留参数，用户无需感知。
- enSequentialWrite（输入）：预留参数，用户无需感知。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Iterate（卷积计算）](iterate.md)（`related`）：本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C Buffer中的数据将被写入目标地址。；在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与［Iterate］(iterate.md)接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵。。Iterate 卡规定先计算并把结果留在 L0C，再由 GetTensorC 卡规定的后继调用把该矩阵块搬到 GM，二者构成有顺序和中间存储契约的配套 API 链。
<!-- cannbot:related:end -->
