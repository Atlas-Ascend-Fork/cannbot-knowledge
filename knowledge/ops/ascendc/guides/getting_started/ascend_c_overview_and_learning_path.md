---
type: Guide
title: Ascend C概述
description: 介绍CANN和Ascend C的定位与多层级API体系，提供从快速入门到高级编程的学习路径导航。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/ascend_c_overview_and_learning_path.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Ascend C概述

## CANN概述
AI（Artificial Intelligence，人工智能）芯片是专为加速人工智能计算任务设计的专用处理器，凭借高度并行化的硬件架构，可高效应对深度学习场景中的大规模张量运算。NPU（Neural-Network Processing Unit，神经网络处理器）作为AI芯片的典型代表，其核心优势在于适配神经网络任务的高效执行；昇腾AI处理器作为专用NPU，内部集成大量高性能计算核心，进一步强化了这一硬件优势，为AI任务的高效运行提供坚实支撑。
在神经网络模型中，算子是构成模型的基础计算单元，封装了针对张量数据的特定数学操作逻辑，如卷积、矩阵乘、激活函数等。神经网络模型的推理与训练过程，本质上是一系列算子按照预设逻辑有序执行、协同完成计算任务的过程。为充分释放昇腾NPU的硬件算力，需构建一套能够高效衔接上层AI框架与底层硬件的软件平台，而CANN（Compute Architecture for Neural Networks）正是华为专为昇腾NPU打造的全栈软件解决方案。
CANN基于分层架构设计，实现了上层应用与底层硬件的无缝衔接。向上，兼容PyTorch等主流AI框架，确保应用层的兼容性与易用性；向下，深度适配昇腾AI处理器，充分发挥硬件的计算潜能，进而构建起CPU与NPU深度融合的异构计算体系。在该体系中，CANN通过Runtime运行时接口驱动CPU与NPU高效协同调度：CPU完成数据准备、任务拆解与调度后，将算子任务下发至NPU加速执行；计算完成后，结果由CPU回收或根据业务需求进行进一步处理。这一协同机制贯穿算子、模型、应用全层级，有效达成计算性能与运行效率的最优平衡，为昇腾AI处理器算力的充分释放提供核心软件支撑。
## Ascend C简介
大模型时代，算力需求正以前所未有的速度激增。如何开发高性能算子，充分释放硬件每一分潜能，已成为决定AI应用落地的关键。为帮助开发者高效构建可直接运行于NPU的高性能算子，Ascend C应运而生。Ascend C是CANN生态下，面向昇腾AI处理器推出的专用算子开发语言，原生兼容C与C++标准规范。此外，Ascend C秉持开放芯片完备编程能力，支撑极致性能的设计理念，构建多层级API体系，满足多场景算子开发诉求，让您能够根据项目需求、团队技能和性能目标，在开发效率与运行性能之间灵活权衡，实现最优平衡。
为满足不同场景的诉求，Ascend C构建了从单指令抽象、单核公共算法到多核算子的多层级API体系，其总体逻辑架构如下：
- 语言扩展层C API：纯C接口，提供数组内存分配、基于指针的计算接口，延续业界熟悉的C编程体验，并完整开放芯片能力。
- 基础API：以单指令为抽象的C++类库，一般基于Tensor编程，并逐步通过Layout完善Tensor编程体验。
- 高阶API：对单核常见算法进行抽象与封装，提供开箱即用的公共算法实现。
- 算子模板库：基于模板提供算子的完整实现参考，降低Tiling开发复杂度，支持用户自定义扩展。
- Python前端PyAsc：基于Python原生接口（参见 PyAsc），提供芯片底层完备编程能力，并将逐步引入Layout化Tensor编程、SIMT编程等，实现用Python开发高性能算子。

<!-- cannbot:related:start -->
## 相关

- [Ascend C多层级编程接口选择参考](../asc_how_to_choose_api.md)（`related`）：Ascend C多层级编程接口选择参考 与《Ascend C概述》的实质衔接是：概述/快速开始解释学习入口，TPipe/TQue 原理与范式对应 choice guide 的易编程层，兼容性策略说明跨代选择接口层时的稳定性成本。
- [环境准备](environment_setup.md)（`related`）：学习路径把环境安装置于 SIMD/SIMT 快速开始之前。
- [异构系统与编程模型](quick_start/heterogeneous_system_and_programming_model.md)（`same_topic`）：异构系统与编程模型 与《Ascend C概述》的实质衔接是：该快速入门从异构系统、host/device 编程模型扩展到 AI Core SIMT、SIMD/SIMT 混合和库 API；这些概述共同解释算子从 host tiling 到 device kernel 的边界。
<!-- cannbot:related:end -->
