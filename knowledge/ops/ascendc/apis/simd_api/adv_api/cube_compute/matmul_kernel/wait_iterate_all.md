---
type: API
title: WaitIterateAll
description: 等待IterateAll异步接口返回，支持连续输出到Global Memory。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitIterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# WaitIterateAll

等待IterateAll异步接口返回，支持连续输出到Global Memory。

函数原型：__aicore__ inline void WaitIterateAll()

约束：
- 配套IterateAll异步接口使用。
- 仅支持连续输出至Global Memory。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：异步：不需要同步等待IterateAll执行结束。；等待IterateAll异步接口返回，支持连续输出到Global Memory。。左卡允许 IterateAll 以 sync=false 发起异步矩阵计算，右卡负责等待该异步调用完成；两端给出发起与完成等待的直接生命周期顺序。
<!-- cannbot:related:end -->
