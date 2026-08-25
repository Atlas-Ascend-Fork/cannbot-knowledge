---
type: Guide
title: Memory矢量计算编程
description: 本文介绍基于统一缓存（Unified Buffer，下文简称UB）的Ascend C矢量计算开发方法，该计算能力简称Memory矢量计算编程，是Ascend
  C中最基础、应用最广泛的矢量编程方式。NPU架构版本2201原生支持完整的UB直接编程能力；NPU架构版本3510引入寄存器计算能力，推荐使用Reg矢量计算编程以获得更高性能。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/memory_vector_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Memory矢量计算编程

本文介绍基于统一缓存（Unified Buffer，下文简称UB）的Ascend C矢量计算开发方法，该计算能力简称Memory矢量计算编程，是Ascend C中最基础、应用最广泛的矢量编程方式。NPU架构版本2201原生支持完整的UB直接编程能力；NPU架构版本3510引入寄存器计算能力，推荐使用Reg矢量计算编程以获得更高性能。
## Memory矢量编程的基本步骤
Memory矢量计算的标准数据流分为数据搬入、计算、数据搬出三个阶段，完整流程如下：
1. 通过DMA将数据从全局内存搬运至本地内存；
2. 进行矢量计算；
3. 计算完成后，通过DMA将结果从本地内存搬运回全局内存（Global Memory）。
## Memory矢量计算内存管理
Memory矢量计算依托本地内存中的UB完成运算，开发者需先将输入数据搬运至UB，再调用矢量计算指令执行计算。UB支持通过数组形式声明，分为静态申请和动态申请两种方式。
- 静态申请：分配固定大小的内存空间，空间尺寸在编译阶段确定，运行时无法修改。
- 动态申请：用户需要通过>>中参数dynamic_ub_size指定动态内存的空间大小，其大小在运行期确定。
## Memory数据搬运
昇腾NPU提供多组专用接口，实现全局内存（GM）与统一缓存（UB）之间的数据搬运，适配各类业务场景。为保障矢量计算效率，标准流程为：数据从GM搬运至UB完成计算，计算结果再从UB回写至GM，形成完整数据链路。
开发者可灵活配置参数，精准控制数据块数量、长度、地址间隔等属性，实现连续数据搬运与非连续（高维切分）数据搬运，充分发挥硬件搬运与计算的协同能力，提升矢量算子整体执行效率。
根据上述矢量搬运能力的描述，开发者可以根据不同的场景选择合适的接口进行处理。
连续搬运: 若需将GM中连续地址的数据搬运至UB，仅需指定搬运数据的字节长度即可。例如将形状为256、数据类型为half的src_gm数据搬入UB，可直接调用asc_copy_gm2ub接口：
> 📌 该接口主要为了提升用户数据搬运的易用性，由软件层面提供，底层通过高维切分接口实现。
非连续搬运: 若需将GM中多段非连续数据搬入同一段UB空间，可通过高维切分模式，配置数据块数量、单块长度、块间间隔等参数。以形状为256、数据类型为half的src_gm为例，对应搬运逻辑与代码实现如下：
> 📌 stride（前一块数据头到后一块数据头的间隔）为该接口从NPU架构版本3510引入，NPU架构版本2201使用gap（前一个数据块结束地址与后一个数据块起始地址的差值）。
非对齐搬运: 基础高维切分接口要求GM的数据长度与地址间隔均按32字节对齐，无法适配非对齐场景。例如将数据改为形状(16, 200)、类型为half的src_gm后，asc_copy_gm2ub无法实现隔行搬运。针对该场景，Ascend C提供asc_copy_gm2ub_align非对齐搬运接口，支持以字节为单位配置数据块长度与地址步长，突破32字节对齐限制。
以上图为例，将两个数据块从GM搬运至UB，每个blockLen为54B，源操作数相邻数据块之间的间隔为1B，目的操作数相邻数据块之间的间隔为32B。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2Ub](../../../../../apis/simd_api/c_api/vector_data_move/asc_copy_gm2ub/asc_copy_gm2ub.md)（`explains`）：Memory矢量计算编程 与《AscCopyGm2Ub》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [AscCopyGm2UbAlign](../../../../../apis/simd_api/c_api/vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`explains`）：Memory矢量计算编程 与《AscCopyGm2UbAlign》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [Memory矢量计算](../../../../../apis/simd_api/basic_api/memory_vector_compute/memory_vector_compute.md)（`explains`）：Memory矢量计算编程 与《Memory矢量计算》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [Memory矢量计算](../../../../../apis/simd_api/c_api/vector_compute/memory_vector_compute.md)（`explains`）：Memory矢量计算编程 与《Memory矢量计算》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [Memory矢量计算接口边界值汇总](../../../../../apis/appendix/memory_vector_compute_interface_boundary_value_summary.md)（`explains`）：Memory矢量计算编程 与《Memory矢量计算接口边界值汇总》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [AI Core SIMD编程模型概述](../overview.md)（`related`）：AI Core SIMD编程模型概述 与《Memory矢量计算编程》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [ASC_VDEQ_SIZE 未声明 — 勿直引 vector_compute.h](../../../../../runbooks/compilation/asc_simd_umbrella_header_for_c_api_symbols.md)（`related`）：Memory矢量计算编程 与《ASC_VDEQ_SIZE 未声明 — 勿直引 vector_compute.h》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [C语言编程概述](c_programming_overview.md)（`same_topic`）：Memory矢量计算编程 与《C语言编程概述》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [MemoryVectorComputation](../cpp_tensor_programming/memory_vector_computation.md)（`same_topic`）：Memory矢量计算编程 与《MemoryVectorComputation》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [TPipe-TQue编程原理介绍](../tpipe_tque_programming/tpipe_tque_principles.md)（`same_topic`）：Memory矢量计算编程 与《TPipe-TQue编程原理介绍》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [TPipe和TQue编程范式](../tpipe_tque_programming/tpipe_tque_paradigm.md)（`same_topic`）：Memory矢量计算编程 与《TPipe和TQue编程范式》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《Memory矢量计算编程》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [核函数（AI Core SIMD编程）](../kernel_function.md)（`same_topic`）：Memory矢量计算编程 与《核函数（AI Core SIMD编程）》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
<!-- cannbot:related:end -->
