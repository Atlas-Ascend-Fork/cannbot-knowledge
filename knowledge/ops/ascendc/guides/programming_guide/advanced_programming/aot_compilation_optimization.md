---
type: Guide
title: AOT编译优化（高级编程）
description: AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aot_compilation_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AOT编译优化

## 概述
AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
## 核心原理
在Ascend C算子开发中，Tiling参数（如矩阵分块大小、操作类型等）通常在运行时由Host侧计算并传入Kernel。通用版本Kernel以变量形式使用这些参数，无法深度优化。
AOT的核心思想是：将特定Tiling配置以编译期常量的形式固化到模板代码中，让编译器在编译阶段就能看到这些值，进一步实现：
- 循环展开：基于常量边界完全展开内层循环，消除循环控制开销。
- 常量传播：在编译期计算所有依赖Tiling常量的表达式，减少运行时的标量计算。
- 死代码消除：根据常量操作类型、分块大小裁剪永远不会执行的条件分支减少执行代码量，降低ICache Miss比率。
## 整体流程
### Kernel常量化预编译
- 根据算子的典型Shape和输入，编写Tiling常量模板定义
- Kernel函数实现，常量Tiling与运行时Tiling变量合一的代码实现
### Host在运行时选择特定Kernel
在Host调用Kernel的代码中加入常量化Tiling匹配和调用，编译器根据指定常量Tiling模板与Kernel混合编译实现常量Kernel实例化。
### 完整示例
一个完整的AOT编译优化Matmul示例可参考 matmul_aot_compilation。该示例演示了纯Cube场景下实现AOT编译的完整流程，并将模板方法进行提取实现了一套简易API。
## 注意事项
1. Tiling字节兼容性：如果算子修改了Tiling结构体，则需要确保定义的常量与当前的Tiling结构体定义一致。
2. 编译时间与二进制体积：每个AOT特化版本都会增加编译时间和二进制体积。建议只针对高频使用的配置预编译AOT版本，避免过度特化。
3. 运行时开销：常量Tiling的匹配过程增加额外Host开销，开发者需结合算子使用场景进行相应调整。

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《AOT编译优化（高级编程）》具体提供“AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [指令双发优化](../../operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)（`related`）：指令双发优化 与《AOT编译优化（高级编程）》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [Matmul性能优化策略总览](../../operator_practice/best_practices/matmul_tuning_cases/matmul_optimization_overview.md)（`same_topic`）：AOT编译优化（高级编程）：AOT把典型Tiling常量化并在host按配置选择特化kernel；编译加速页给构建上下文，多分支策略承接运行时选择，Matmul优化页对应正文点名示例。 目标卡《Matmul性能优化策略总览》补充：本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各分类的简介请参见如下表格，详细内容请阅读后续章节。
- [多分支策略](aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`same_topic`）：AOT编译优化（高级编程）：AOT把典型Tiling常量化并在host按配置选择特化kernel；编译加速页给构建上下文，多分支策略承接运行时选择，Matmul优化页对应正文点名示例。 目标卡《多分支策略》补充：本文属于扩展内容，介绍同一个算子需要根据dtype、shape或属性执行不同计算流程时，如何使用TilingKey或Kernel模板组织多个Kernel分支。TilingKey使用数字标识分支，适合分支数量较少、含义稳定的场景；Kernel模板使用具名参数描述分支，适合由多个维度共同决定分支的场景。
- [高级编程编译加速](aclnn_operator_development/compilation_and_deployment/compilation_acceleration.md)（`same_topic`）：AOT编译优化（高级编程）：AOT把典型Tiling常量化并在host按配置选择特化kernel；编译加速页给构建上下文，多分支策略承接运行时选择，Matmul优化页对应正文点名示例。 目标卡《高级编程编译加速》补充：本文是扩展内容，介绍如何降低算子工程的编译耗时。算子工程编译耗时主要来自Kernel侧代码的逐芯片、逐TilingKey编译；本文从缓存复用、选择性编译、并行度和增量构建四个维度给出加速方案。
<!-- cannbot:related:end -->
