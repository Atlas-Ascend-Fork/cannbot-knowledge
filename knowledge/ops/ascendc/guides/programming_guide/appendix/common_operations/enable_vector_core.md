---
type: Guide
title: EnableVectorCore
description: 针对Atlas推理系列产品，通过宏启用Vector Core，算子执行时同时启动AI Core和Vector Core并行执行相同核函数代码，缓解Vector计算瓶颈。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/common_operations/enable_vector_core.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 如何在矢量编程时启用Vector Core

针对Atlas 推理系列产品，其硬件架构除了AI Core外，还额外设置了单独的Vector Core，作为AI Core中Vector计算单元的补充，从而缓解Vector计算瓶颈。Vector Core只包括了两种基础计算资源：向量计算单元（Vector Unit）和标量计算单元（Scalar Unit），分别用于完成向量与标量的数据计算。矢量算子开发时，启用Vector Core，算子执行时会同时启动AI Core和Vector Core，这些核并行执行相同的核函数代码。
本节将重点介绍如何启用Atlas 推理系列产品中的Vector Core。学习本节内容之前，建议您先熟悉算子实现、基于样例工程完成Kernel直调、工程化算子开发的相关内容，掌握基于AI Core的算子端到端开发流程。在此基础上本章将重点阐述启用Vector Core时的差异点。具体如下：
1.  完成算子kernel侧开发时，需要通过宏KERNEL_TASK_TYPE_DEFAULT启用Vector Core，算子执行时会同时启动AI Core和Vector Core，此时AI Core会当成Vector Core使用。如下的代码样例展示了启用Vector Core的方法：
2.  完成host侧tiling开发时，设置的numBlocks代表的是AI Core和Vector Core的总数，比如用户在host侧设置numBlocks为10，则会启动总数为10的AI Core和Vector Core；为保证启动Vector Core，设置数值应大于AI Core的核数。您可以通过GetCoreNumAic接口获取AI Core的核数，GetCoreNumVector接口获取Vector Core的核数。如下代码片段，分别为使用kernel直调工程和自定义算子工程时的设置样例，此处设置为AI Core和Vector Core的总和，表示所有AI Core和Vector Core都启动。
-   kernel直调工程
-   自定义算子工程

<!-- cannbot:related:start -->
## 相关

- [block 数应覆盖可用 Vector 核](../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`related`）：“设置的numBlocks代表的是AI Core和Vector Core的总数”给出启用 Vector Core 时 host tiling 的计数语义；“host 将 `numBlocks` 硬封顶为 `C_old`，而目标设备实测 `V_measured > C_old`”展示固定上限如何造成实际 Vector 核闲置。
<!-- cannbot:related:end -->
