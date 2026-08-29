---
type: API
title: SetTail
description: 在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTail.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetTail

在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。

函数原型：__aicore__ inline void SetTail(int tailM = -1, int tailN = -1, int tailK = -1)

参数：
- tailM（输入）：重新设置的singleCoreM值
- tailN（输入）：重新设置的singleCoreN值
- tailK（输入）：重新设置的singleCoreK值

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [多核非对齐切分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_unaligned_split.md)（`explains`）：调用SetTail接口重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，在处理尾块的时候按照设置的值也就是tailM/tailN/tailK进行搬运和计算。；在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。；Guide 的非对齐尾块步骤直接调用该 API 合同。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。；在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。；两接口调整同一 Matmul 对象的单核 M/N/K 形状；SetSingleShape 正文明示与 SetTail 功能一致并给出推荐替代。
<!-- cannbot:related:end -->
