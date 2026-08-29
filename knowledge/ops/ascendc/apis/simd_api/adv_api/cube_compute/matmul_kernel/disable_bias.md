---
type: API
title: DisableBias
description: 清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/DisableBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DisableBias

清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。

函数原型：__aicore__ inline void DisableBias()

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [ClearBias](clear_bias.md)（`same_topic`）：DisableBias接口与该接口的功能相同，建议使用DisableBias。 清除Bias标志位，表示Matmul计算时没有Bias参与。；清除Bias标志位，表示Matmul计算时没有Bias参与。。焦点卡明确将同功能旧入口迁移为候选 DisableBias。
<!-- cannbot:related:end -->
