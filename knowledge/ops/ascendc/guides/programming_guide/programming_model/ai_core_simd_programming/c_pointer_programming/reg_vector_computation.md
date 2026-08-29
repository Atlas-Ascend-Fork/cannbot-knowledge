---
type: Guide
title: Reg矢量计算编程（C指针编程）
description: '> 📌 提示：Reg矢量编程仅在NPU架构版本3510进行SIMD矢量计算编程时支持。'
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/reg_vector_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Reg矢量计算编程

> 📌 提示：Reg矢量编程仅在NPU架构版本3510进行SIMD矢量计算编程时支持。
本文介绍如何在Ascend C中使用语言扩展C API进行寄存器级矢量计算编程，该能力面向已经熟悉Ascend C编程模型的开发者。这种基于硬件寄存器的编程方式称为Reg矢量计算编程。
## 为什么需要Reg矢量编程
### Memory矢量计算的瓶颈
在以往的SIMD矢量编程中，矢量计算单元的源操作数和目的操作数都直接落在LocalMemory（Unified Buffer，以下简称UB）上。每一条矢量计算的执行过程都包含"从UB读 → 在执行单元算 → 写回UB"。当一个算子由多个矢量计算串联组成时（例如dst = (a + b) * c + d），每一步的中间结果都必须先写回UB，再被下一条指令重新读出。
这种模式下存在三个典型瓶颈：
- UB读写带宽被反复占用：中间结果在UB上往返，访存压力随着矢量计算增加而线性放大。
- UB Bank冲突严重：对UB的反复读写，极大增加了UB Bank冲突的概率。
- 关键路径被访存拉长：当计算指令执行时间很短，整体耗时会被UB读写时间占用。
这种“每步落地UB”的开销会成为优化的天花板。
### Reg矢量计算的定位
为了突破上述Memory矢量编程瓶颈限制，NPU架构版本3510在硬件中新增了一级缓存SIMD Register File（以下简称寄存器）这一级存储；Reg矢量编程正是面向这一级寄存器的编程方式。其核心思想是：将一段连续的矢量计算保留在寄存器中完成，仅在进入和退出这段计算时与UB交互一次，中间结果可不再回写UB。
Reg矢量计算与Memory矢量计算的对比如下：
维度：Memory矢量计算：Reg矢量计算
数据位置：UB：SIMD Registers
中间结果：必须回写UB：可在寄存器中连续消费
使用成本：较低：较高（需要理解寄存器等相关操作）
适用目标：快速实现、不追求极致性能：追求极致性能、可接受更高代码复杂度
在开放寄存器编程的硬件上，同时提供Memory矢量计算接口，保持与前序代际硬件兼容。在Memory矢量计算接口内部实现软件封装的Reg矢量计算。
### 适用场景
当以下条件同时满足时，建议考虑使用Reg矢量编程：
1. 目标设备支持Reg矢量编程。
2. 核心耗时集中在连续矢量计算上。
3. 中间结果在UB中存在明显的反复读写。
4. 追求极致性能收益，可接受更高的代码复杂度。
## 硬件原理
### SIMD Register File与执行单元
AIV是AI Core内用于矢量计算的核，核内参与Reg矢量计算的硬件单元包括：
- Reg矢量执行单元：用于执行Reg矢量计算，从寄存器读取数据，完成计算后将结果写回寄存器。
- DMA单元：用于执行Reg矢量搬运，负责在寄存器和UB之间搬运数据。
- Aux Scalar：处理Reg矢量执行单元和Reg搬运单元所需的标量计算（例如地址计算）。
Reg矢量执行单元、DMA单元和Aux Scalar虽属于不同的硬件执行单元，但是在实际执行时都归属PIPE_V流水。
