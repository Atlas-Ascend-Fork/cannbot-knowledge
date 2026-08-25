---
type: API
title: GetOffsetC
description: 预留接口，为后续功能做预留。 获取本次计算时当前分片在整个C矩阵中的位置。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetOffsetC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetOffsetC

预留接口，为后续功能做预留。 获取本次计算时当前分片在整个C矩阵中的位置。

函数原型：__aicore__ inline MatrixOffset GetOffsetC()

返回值：MatrixOffset结构体如下：

<!-- cannbot:related:start -->
## 相关

- [GetTensorC](get_tensor_c.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《GetOffsetC》说明预留接口，为后续功能做预留。 获取本次计算时当前分片在整个C矩阵中的位置。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Iterate](iterate.md)（`same_topic`）：GetOffsetC 与《Iterate》的实质衔接是：GetOffsetC 返回当前 Matmul 分片在完整 C 矩阵的位置；Iterate 推进分片，GetTensorC 消费结果，Kernel/使用说明给出该预留位置信息所在的执行链。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：GetOffsetC 与《Matmul Kernel侧接口》的实质衔接是：GetOffsetC 返回当前 Matmul 分片在完整 C 矩阵的位置；Iterate 推进分片，GetTensorC 消费结果，Kernel/使用说明给出该预留位置信息所在的执行链。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：GetOffsetC 与《Matmul使用说明》的实质衔接是：GetOffsetC 返回当前 Matmul 分片在完整 C 矩阵的位置；Iterate 推进分片，GetTensorC 消费结果，Kernel/使用说明给出该预留位置信息所在的执行链。
<!-- cannbot:related:end -->
