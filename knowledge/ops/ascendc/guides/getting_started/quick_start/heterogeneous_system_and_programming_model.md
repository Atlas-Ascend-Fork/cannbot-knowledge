---
type: Guide
title: 异构系统与编程模型
description: '> 本文作为算子编程快速入门章节，将从昇腾异构系统基础入手，逐步拆解编程模型核心要素，帮助您快速建立昇腾算子编程的整体认知，为后续实操开发奠定基础。'
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/heterogeneous_system_and_programming_model.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 异构系统与编程模型

> 本文作为算子编程快速入门章节，将从昇腾异构系统基础入手，逐步拆解编程模型核心要素，帮助您快速建立昇腾算子编程的整体认知，为后续实操开发奠定基础。
---
## 什么是异构系统？
基于昇腾处理器的异构系统，核心是通过两类功能互补的处理器协同工作，兼顾通用计算与高密度并行计算，实现整体性能最优。
角色：组成：职责
Host（主机）：CPU + Host Memory：通用计算、资源管理、任务调度、统筹协调
Device（设备）：昇腾NPU + Device Memory：高密度并行计算（深度学习推理/训练、图像处理等）
> 💡 通俗理解：Host如同项目经理，负责规划、分配、协调；Device如同专业工程师团队，专注于高效完成高强度、重复性的计算工作。两者分工协作，提升整体效率。
---
## 昇腾应用程序的组成
基于昇腾异构系统的应用程序必然包含两部分代码，分工明确、协同运行：
代码类型：运行位置：编程语言：核心职责
Host代码：CPU（Host侧）：标准C/C++：管理Device设备、搬运数据、启动NPU任务、同步状态
Device代码：NPU（Device侧）：Ascend C：执行具体的并行计算任务，称为核函数
> ✅ 便捷提示：Host代码与Device代码可编写在同一个.asc文件中，由毕昇编译器自动识别、分别编译，简化开发流程。
---
## Host与Device的协作流程
Host侧通过调用CANN Runtime API完成与Device的协同工作。典型流程如下：
1. 分配内存：在Device Memory中申请输入/输出所需的空间。
2. 数据搬入：将输入数据从Host Memory拷贝到Device Memory（数据需进入Device侧才能被NPU访问）。
3. 启动NPU计算任务：调用Device侧预先编写的核函数，NPU开始并行计算。
4. 同步等待：Host端等待NPU执行完成，确保数据计算完整（避免未完成就读取结果）。
5. 数据搬出：将计算结果从Device Memory拷贝回Host Memory，供后续处理。
> 📌 关键点：Host与NPU是异步执行的，第4步的同步必不可少，否则可能读取到未完成的数据。
---
## AI Core：NPU的核心计算单元
NPU是Device侧的计算核心，而 AI Core则是NPU内部的“最小计算单元”。一枚NPU芯片通常集成多个AI Core，可并行处理不同的数据块，大幅提升整体计算吞吐量。
每个AI Core内部结构高度优化，专门适配并行计算需求，核心组件包括：
- 标量处理单元：处理控制流（如分支、循环）和地址计算，类似传统CPU核心，是AI Core的“控制核心”。
- 向量处理单元：执行向量运算，是SIMD/SIMT两种并行模型的主要载体。不同昇腾芯片架构对两种模式的支持有所差异。
