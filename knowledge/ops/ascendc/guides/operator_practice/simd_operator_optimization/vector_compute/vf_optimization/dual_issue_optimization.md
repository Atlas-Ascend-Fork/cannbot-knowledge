---
type: Guide
title: 指令双发优化
description: 指令双发指的是处理器在同一个时钟周期内，能够同时发射两条指令到执行单元进行处理。这种能力需要满足以下两个条件：
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 指令双发优化

指令双发指的是处理器在同一个时钟周期内，能够同时发射两条指令到执行单元进行处理。这种能力需要满足以下两个条件：
-   两条指令之间没有数据上的依赖关系（依赖关系指后一条指令需要使用前一条指令产生的结果）
-   硬件中拥有足够的执行资源
这种机制可以在不改变程序逻辑的前提下，提升处理器在单位时间内的指令处理效率，是实现指令级并行的重要基础之一。
如下示例中，VLoop-1循环16次，由于每个循环内的4条指令有数据依赖，所以执行队列的深度是64，循环内指令无法实现双发。指令基于循环展开后，64条指令并发执行顺序如下图所示，LoadAlign_0和LoadAlign_1没有依赖关系，可以并发执行。黑框选中的位置仅代表该4条指令有同时执行的资格，真正执行时是乱序选取其中的2条执行。
在编写算子时，开发者通常习惯于按“加载数据 → 处理计算 → 存储结果”的顺序来组织代码流程。这种写法在寄存器资源充足时运行良好，但一旦资源紧张，问题就会被放大。当多个计算指令之间会产生依赖关系，这些等待会堆积在执行队列中，导致后续指令无法及时发射。
开发者在编程时应尽可能保证队列里存在数目充足且无依赖的并发指令，从而高效的利用硬件双发特性。可以通过合理拆分VF循环以及手动控制循环展开等方案来提高性能。
## 合理拆分VF循环
VF并不是写的越长，把所有运算都放在一个for循环内就好，需要适当的搬出中间结果到UB，减少数据依赖。
优化前：
优化后：
## 手动控制循环拆分
如果循环内存在依赖关系过多的指令，队列没有办法同时加载进for(i = n)和for(i = n+1)的所有指令，那么即使循环之间没有依赖关系，也无法启用双发特性，指令无法并发执行。可以通过手动展开循环，这样做有两个好处：贴近硬件乱序执行的特性，为下发的指令创造更多执行的机会；减少指令因为寄存器资源未到位而产生的等待。
当前支持以下两种展开方式：
展开方式：开启方式：优点：缺点
:--：:--：:--：:--
手动展开VF循环：/：&bull;自主可控；&bull;能处理复杂循环或src/dst寄存器复用等场景；：&bull;代码复杂度高；
编译器自动展开：#pragma unroll number （number表示展开层数）：&bull;代码复杂度低；：&bull;src/dst寄存器复用时无法展开。
### 手动展开VF循环
展开后
### 编译器自动展开
## 避免寄存器数量超限，导致执行队列中依赖指令的数量增加
在同一个VF中，硬件可以同时处理的最大RegTensor寄存器个数为32，如果超出，编译器会进行数据的换入换出并加入同步指令，严重拖慢算子的执行效率。
在同一个VF中，MaskReg数量上限为8个，超过8个会产生性能劣化。
在同一个VF中，AddrReg数量上限为8个，超过8个会产生性能劣化。
在同一个VF中，读写寄存器UnalignRegForLoad、UnalignRegForStore的数量上限均为4个，若实际使用超过4个UnalignRegForLoad或UnalignRegForStore会直接导致编译失败。
优化方案：
-   使用布尔代数运算。

<!-- cannbot:related:start -->
## 相关

- [AddrReg](../../../../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/addr_reg.md)（`explains`）：指令双发优化 与《AddrReg》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [Reg矢量计算接口指令单双发汇总](../../../../../apis/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md)（`explains`）：指令双发优化 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [AOT编译优化（高级编程）](../../../../programming_guide/advanced_programming/aot_compilation_optimization.md)（`related`）：指令双发优化 与《AOT编译优化（高级编程）》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [SIMD算子优化概述](../../memory_access/avoid_ub_bank_conflict/overview.md)（`related`）：指令双发优化 与《SIMD算子优化概述》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [VfFusionOptimization](vf_fusion_optimization.md)（`related`）：指令双发优化 与《VfFusionOptimization》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [VfLoopOptimization](vf_loop_optimization.md)（`related`）：指令双发优化 与《VfLoopOptimization》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [中级性能优化](../../../typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《指令双发优化》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [中级性能优化](../../../typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《指令双发优化》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [优化建议总览表（SIMD算子优化）](../../optimization_summary.md)（`related`）：指令双发优化 与《优化建议总览表（SIMD算子优化）》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [原子操作指令优化](../../../simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`related`）：指令双发优化 与《原子操作指令优化》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [基于全局掩码复用的计算性能优化](../mask_reuse_optimization.md)（`related`）：指令双发优化 与《基于全局掩码复用的计算性能优化》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [设置DCI编译选项来减少算子尾开销](../../overhead_optimization/dci_compile_option.md)（`related`）：指令双发优化 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [高阶极限打磨](../../../typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/extreme_optimization.md)（`same_topic`）：GELU 卡通过展开多组依赖链提升双发机会，双发优化指南提供其指令依赖和调度原理。
<!-- cannbot:related:end -->
