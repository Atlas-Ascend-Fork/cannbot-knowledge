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

- [ClearBias](clear_bias.md)（`same_topic`）：DisableBias 与《ClearBias》的实质衔接是：DisableBias、ClearBias、SetBias 和 EnableBias 改变同一 Matmul 对象的 bias 状态，适用于迭代间切换。
- [EnableBias](../matmul_tiling/enable_bias.md)（`same_topic`）：DisableBias 与《EnableBias》的实质衔接是：DisableBias、ClearBias、SetBias 和 EnableBias 改变同一 Matmul 对象的 bias 状态，适用于迭代间切换。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；DisableBias正文界定“清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
- [SetBias](set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；DisableBias正文说明“清除Bias标志位，表示Matmul计算时没有Bias参与。如果在初始化时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
<!-- cannbot:related:end -->
