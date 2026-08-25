---
type: API
title: SetBatchNum
description: 在不改变Tiling的情况下，重新设置多Batch计算的Batch数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetBatchNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetBatchNum

在不改变Tiling的情况下，重新设置多Batch计算的Batch数。

函数原型：__aicore__ inline void SetBatchNum(int32_t batchA, int32_t batchB)

参数：
- batchA（输入）：设置的一次计算的A矩阵Batch数。
- batchB（输入）：设置的一次计算的B矩阵Batch数。

约束：
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。
- 本接口仅支持在纯Cube模式（只有矩阵计算）下调用。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
