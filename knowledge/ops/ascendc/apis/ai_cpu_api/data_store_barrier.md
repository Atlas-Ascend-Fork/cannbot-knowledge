---
type: API
title: DataStoreBarrier
description: 数据同步屏障指令，该指令会阻塞当前线程执行，确保所有先前的写内存操作完成并对其它硬件单元可见后，才继续执行后续指令。用于AI CPU与AI
  Core多核之间的数据一致性。
tags: [task.lookup, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/DataStoreBarrier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DataStoreBarrier

数据同步屏障指令，该指令会阻塞当前线程执行，确保所有先前的写内存操作完成并对其它硬件单元可见后，才继续执行后续指令。用于AI CPU与AI Core多核之间的数据一致性。

约束：
- 该接口仅支持通过>>调用，并在异构编译场景使用。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AI CPU算子编译](../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md)（`explains`）：DataStoreBarrier 只能通过 >> 在异构编译场景调用；AI CPU 算子编译说明补齐 .aicpu/.asc 双文件、libaicpu_api 链接和 >> 调用的构建契约。
- [AI CPU编程（编程模型）](../../guides/programming_guide/programming_model/ai_cpu_programming.md)（`explains`）：AI CPU 编程指南说明 AI CPU 与 AI Core 共享 Device 内存访问能力以及 >> 核函数调用模型，解释了 DataStoreBarrier 跨两类核保证写可见性的运行环境。
<!-- cannbot:related:end -->
