---
type: API
title: ClearBias
description: DisableBias接口与该接口的功能相同，建议使用DisableBias。 清除Bias标志位，表示Matmul计算时没有Bias参与。如果在调用Init时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/ClearBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# ClearBias

DisableBias接口与该接口的功能相同，建议使用DisableBias。 清除Bias标志位，表示Matmul计算时没有Bias参与。如果在调用[Init](init.md)时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。

函数原型：__aicore__ inline void ClearBias()

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：ClearBias 明确用于覆盖 Init 时 TCubeTiling.isBias 启用的 Bias 状态，理解 Init 的资源/tiling 初始化是判断清除动作何时生效的前置。
- [SetBias](set_bias.md)（`related`）：SetBias 设置 Bias 输入，ClearBias/DisableBias 则撤销该参与标志；二者是同一 Matmul 对象 Bias 状态的相反控制动作。
- [DisableBias](disable_bias.md)（`same_topic`）：DisableBias 与《ClearBias》的实质衔接是：DisableBias、ClearBias、SetBias 和 EnableBias 改变同一 Matmul 对象的 bias 状态，适用于迭代间切换。
<!-- cannbot:related:end -->
