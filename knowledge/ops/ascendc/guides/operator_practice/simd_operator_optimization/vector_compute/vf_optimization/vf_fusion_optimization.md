---
type: Guide
title: VfFusionOptimization
description: 将多个VF函数融合成一个VF函数以提升性能，编译器通过Loop Fuse算法自动执行浅度融合、深度融合和VF内自动同步。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/vf_fusion_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# VF融合优化

【优先级】高
【描述】VF融合是将代码中多个VF函数融合成一个VF函数，有效提升性能。VF融合特性是优化特性，VF自动融合会借助Loop Fuse算法，将VF转换成Loop形态，然后将控制流等价（Control-Flow-Equivalent）的VF进行融合，最后将VF进行还原。编译器首先会做融合前的合法性检查，判断两个VF是否等价，Main侧中间代码是否能在VF内执行以及融合后是否可产生正收益（不会引起传参寄存器溢出、VF代码不会过大）等，如果满足VF融合条件，编译器会自动执行VF融合优化，为保证融合后的VF执行逻辑与语义与融合前一致，会在原来两个VF之间保守地插入同步指令，编译器还会尝试外提、合并融合后的VF中的指令，对VF代码进行优化。融合策略是能融尽融，用户按照符合融合的合法性检查的模式进行编码，可以增加VF融合的机会。
## VF融合原理介绍
VF融合优化可分为三个阶段：VF浅度融合、VF深度融合和VF内自动同步：
VF浅度融合：编译器首先会分析两个VF的控制流是否等价，构建Cost Model分析是否有正向收益，如果满足VF融合条件，将VF外部的控制流融入到VF内，将VF外的Software Loop硬化成VF内的Hardware Loop，然后开启VF自动融合的基础能力，将两个VF融合成一个VF，为后续的VF深度融合提供基础。
VF深度融合：VF深度融合会继续对VF内的Hardware Loop进行融合，从而减少Hardware Loop的启动开销，并且极大地减少冗余的Load/Store操作，充分复用寄存器。
VF内自动同步：编译器会精准地插入必要的同步指令，删除冗余的同步指令，极大地释放了硬件OOO（Out of Order）能力。用户无需手动插入同步指令，极大地降低了用户的编码难度。
## VF融合编写指导
1.  多个VF函数自动融合：如果多个VF函数的控制流等价，且满足均为Hardware Loop循环，编译器会执行VF融合优化特性。
【正例】VF函数DivVF和AddVF会被编译器融合成一个VF函数，并且能优化多余的Load/Store指令。
2.  使用基础API连续计算模式：基础API实现对硬件能力的抽象，开放芯片的能力，保证完备性和兼容性。基础API根据对数据操作方法的不同，可以分为两大类：
-   连续计算API：支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维tensor的连续计算问题。
-   高维切分API：支持Repeat和Stride。功能灵活的计算API，提供与Builtin API完全对等的编程能力，充分发挥硬件优势，支持对每个操作数的DataBlock Stride，Repeat Stride，Mask等参数的操作。
在VF融合优化中，推荐使用基础API的连续计算模式编写算子，可以充分发挥出VF融合优化的能力，与高维切分API相比，连续计算API使得编译器能更好地分析VF融合优化，更加容易满足VF融合优化的条件，使用基础API的连续计算模式能写出性能更优的算子。

<!-- cannbot:related:start -->
## 相关

- [VfLoopOptimization](vf_loop_optimization.md)（`related`）：“如果多个VF函数的控制流等价，且满足均为Hardware Loop循环，编译器会执行VF融合优化特性。”与“当VF函数中的循环满足Hardware Loop编码规范时，会被编译器优化为Hardware Loop，提升整体执行性能；否则循环逻辑会由迭代变量和条件判断语句构成Software Loop，无法开启VF循环优化。”提供双方正文证据。融合指南把两端均为 Hardware Loop 作为自动 VF 融合条件，循环指南给出生成 Hardware Loop 的成功与回退判据，组成先规范循环再获得融合的优化链。
- [双 VF 融合输出非预期 先排 CopyOut slot 勿用 PRINTF](../../../../../runbooks/precision/vf_fusion_output_unexpected_check_copyout_slot_not_printf.md)（`related`）：真因是 CopyOut slot 指向错误 buffer（B2 而非 B1）；编译器首先会做融合前的合法性检查。指南说明 VF 融合的合法性、收益与自动同步，Runbook 则给出融合实现输出异常时先排 CopyOut 映射和禁用 VF 内 PRINTF 的验证顺序，避免把非 VF 错误误判为融合机制缺陷。
<!-- cannbot:related:end -->
