---
type: Guide
title: 抽象硬件架构（SIMD与SIMT混合编程）
description: Ascend C支持SIMD与SIMT混合编程，实现向量级并行与线程级并行的高效协同。AI Core包含AIC和AIV，其中AIV核支持SIMT、SIMD两种工作模式，因此可以实现AIV内SIMD与SIMT的混合编程，也支持AIV的SIMT与AIC的SIMD融合编程，整体硬件架构如下图所示：
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/abstract_hardware_architecture.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 抽象硬件架构

Ascend C支持SIMD与SIMT混合编程，实现向量级并行与线程级并行的高效协同。AI Core包含AIC和AIV，其中AIV核支持SIMT、SIMD两种工作模式，因此可以实现AIV内SIMD与SIMT的混合编程，也支持AIV的SIMT与AIC的SIMD融合编程，整体硬件架构如下图所示：

**图1** SIMD与SIMT混合编程硬件架构示意图

## Vector Function工作机制

如上图硬件架构所示，AIV核的计算单元包括SIMD和SIMT两种。针对这两种硬件计算单元，Ascend C抽象出了Vector Function的软件概念，用于表示在SIMT或SIMD硬件计算单元上执行的特定功能代码段。用户通过编写SIMD Vector Function或SIMT Vector Function来调用对应的执行单元完成计算任务，在算子核函数中调用不同类型的Vector Function，以实现SIMD/SIMT硬件单元的切换使用。

如下图所示，simt_func表示在SIMT硬件单元上执行的代码段，simd_func表示在SIMD硬件单元上执行的代码段，代码段属性通过__simt_vf__、__simd_vf__来标识。

**图2** SIMD与SIMT混合编程VF示意图

AIV执行时，Scalar计算单元会将Vector Function发射到Vector Function Queue中，后续串行执行每个Vector Function，并与MTE异步执行。

### SIMD Vector Function

当AIV核处于SIMD工作模式时，执行模型遵从Reg矢量计算方式，核内参与Reg矢量计算的硬件单元包括：

- **Reg矢量执行单元**：用于执行Reg矢量计算，从寄存器读取数据，完成计算后将结果写回寄存器。
- **DMA单元**：用于执行Reg矢量搬运，负责在寄存器和UB之间搬运数据。
- **Aux Scalar**：处理Reg矢量执行单元和Reg搬运单元所需的标量计算（例如地址计算）。

Reg矢量执行单元、DMA单元和Aux Scalar虽属于不同的硬件执行单元，但是在实际执行时都归属PIPE_V流水。这一架构带来两个直接结果：

1. 有寄存器依赖时，由硬件按指令顺序保证数据依赖正确性，用户无需显式插入同步；但跨寄存器对同一UB区域的读写需要显式插入同步，搬运单元与计算单元之间没有自动顺序约束。
2. Reg矢量执行单元和DMA单元在没有数据依赖时可以**同时发射、并行执行**。

**图3** SIMD Reg矢量计算示意图

### SIMT Vector Function

当AIV核处于SIMT工作模式时，执行模型遵从由Thread、Block、Grid组成的线程架构。一个SIMT VF对应一个线程块（Block）的执行上下文，线程块内线程按线性线程号划分为多个Warp，每个Warp包含32个线程。

Warp内线程共享同一条指令流，各线程维护独立的线程索引、寄存器和栈等执行状态。硬件根据线程活跃掩码发射指令：当Warp内线程控制流一致时，可保持较高执行效率；发生分支发散时，硬件会按不同分支路径分批执行活跃线程，有效并行度随之下降。

**图4** SIMT线程架构示意图

<!-- cannbot:related:start -->
## 相关

- [SIMD与SIMT混合算子性能优化概述](../../../../operator_practice/simd_simt_hybrid_optimization/overview.md)（`related`）：SIMD与SIMT混合算子性能优化概述说明AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适合处理分支判断、索引映射、离散访存等不规则逻辑，在程序中结合使用两种编程方式，可以兼顾硬件高吞吐和编程灵活性；对抽象硬件架构（SIMD与SIMT混合编程）而言，混合编程概述定义 SIMD/SIMT 分工，性能章节给出分支与访存选择，SIMT 分支实现卡提供落地接口。
- [SIMD与SIMT混合编程概述](overview.md)（`related`）：SIMD与SIMT混合编程概述说明为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型；对抽象硬件架构（SIMD与SIMT混合编程）而言，混合编程概述定义 SIMD/SIMT 分工，性能章节给出分支与访存选择，SIMT 分支实现卡提供落地接口。
- [通过SIMT实现分支判断](../../../../operator_practice/simd_simt_hybrid_optimization/compute_optimization/simt_branch_judgment.md)（`related`）：通过SIMT实现分支判断说明>该性能优化建议适用于如下型号：；对抽象硬件架构（SIMD与SIMT混合编程）而言，混合编程概述定义 SIMD/SIMT 分工，性能章节给出分支与访存选择，SIMT 分支实现卡提供落地接口。
- [基本架构（硬件实现）](../../hardware_implementation/basic_architecture.md)（`same_topic`）：混合编程架构页在同一 AI Core 上展开 SIMD/SIMT 单元与调度关系，是基础架构的具体编程视角。
- [抽象硬件架构（AI Core SIMD编程）](../../../programming_model/ai_core_simd_programming/abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《抽象硬件架构（SIMD与SIMT混合编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
<!-- cannbot:related:end -->
