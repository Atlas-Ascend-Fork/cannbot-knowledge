---
type: API
title: SetSingleShape
description: 设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetSingleShape

设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。

函数原型：__aicore__ inline void SetSingleShape(int singleM, int singleN, int singleK)

参数：
- singleM（输入）：设置的singleCoreM大小，单位为元素。
- singleN（输入）：设置的singleCoreN大小，单位为元素。
- singleK（输入）：设置的singleCoreK大小，单位为元素。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetTail](set_tail.md)（`same_topic`）：设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。；在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。；两接口调整同一 Matmul 对象的单核 M/N/K 形状；SetSingleShape 正文明示与 SetTail 功能一致并给出推荐替代。
<!-- cannbot:related:end -->
