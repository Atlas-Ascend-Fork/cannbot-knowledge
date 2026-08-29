---
type: API
title: WaitIterateBatch
description: 等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitIterateBatch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# WaitIterateBatch

等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。

函数原型：__aicore__ inline void WaitIterateBatch()

约束：
- 配套IterateBatch或IterateNBatch异步接口使用。
- 仅支持连续输出至Global Memory。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [IterateBatch](iterate_batch.md)（`related`）：“等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。”与“异步场景需要配合WaitIterateBatch接口使用。”分别给出两端正文事实；WaitIterateBatch 是 IterateBatch 异步提交的明确等待端，联合阅读可确定 sync/waitIterateBatch 参数与完成点的正确组合。
<!-- cannbot:related:end -->
