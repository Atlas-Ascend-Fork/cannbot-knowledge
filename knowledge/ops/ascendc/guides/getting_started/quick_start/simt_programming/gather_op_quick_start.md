---
type: Guide
title: Gather算子快速入门
description: 本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/simt_programming/gather_op_quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Gather算子快速入门

本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
开始前请参考环境准备安装所需的CANN软件包，完整样例请见Gather。
- Gather算子功能介绍：
Gather算子的数学表达式为：
计算逻辑：根据索引张量index中的每个元素，从一维输入向量input中采集对应位置的数据，并写入输出张量output。
- 算子设计：
- Device端核函数编程接口
- 核函数定义：通过__global__修饰符声明。
- 数据划分：使用内置变量threadIdx、blockIdx、blockDim计算线程索引，并为每个线程分配需要处理的数据元素。
- 数据搬入：无需额外接口，直接通过指针访问即可。
- 数据计算：根据index中的索引值及操作符[]读取输入数据。
- 数据搬出：无需额外接口，直接通过指针访问即可。
- Host端运行时接口
- 内存分配：使用aclrtMallocHost分配Host Memory，aclrtMalloc分配Device Memory。
- 数据搬入：使用aclrtMemcpy将输入数据从Host Memory拷贝到Device Memory。
- 启动NPU计算任务：通过>>语法糖启动核函数。
- 同步等待：调用aclrtSynchronizeStream等待当前Stream上的任务完成，或调用aclrtSynchronizeDevice等待Device上所有任务完成。
- 数据搬出：使用aclrtMemcpy将计算结果从Device Memory拷贝回Host Memory。
- 算子代码实现：
后缀名为*.asc的代码文件包含Host端与Device端代码。
- Device端Kernel实现：
Device端部分示例如下：
- Host端代码实现：
Host端通过>>语法糖调用Device端代码。
- 算子编译与运行：
CMake配置文件示例：
编译并执行：
如需进一步了解Ascend C的SIMD与SIMT编程模型，请参阅Ascend C编程模型概述。

<!-- cannbot:related:start -->
## 相关

- [AscGather](../../../../apis/simd_api/c_api/vector_compute/asc_gather.md)（`explains`）：AscGather 与《Gather算子快速入门》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`related`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather算子快速入门》明确提供“本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [SIMT API 未进入 AscendC 命名空间导致编译失败](../../../../runbooks/compilation/simt_api_is_in_ascendc_simt_namespace.md)（`related`）：Gather算子快速入门 与《SIMT API 未进入 AscendC 命名空间导致编译失败》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [SIMT 核类型推导失败 — 补 __vector__](../../../../runbooks/compilation/direct_launch_kernel_requires_vector_qualifier.md)（`related`）：Gather算子快速入门 与《SIMT 核类型推导失败 — 补 __vector__》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [dav-3510 GM_ADDR static_cast 编译失败](../../../../runbooks/compilation/gm_addr_cast_from_void_uses_toolchain_cast.md)（`related`）：Gather算子快速入门 与《dav-3510 GM_ADDR static_cast 编译失败》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`related`）：Gather算子快速入门 与《dim3 未声明：显式引入 SIMT 公共头》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`related`）：Gather算子快速入门 与《纯 SIMT kernel 形参 __gm__ 导致编译失败》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [随机 Gather 每元素 DMA 过慢—改 SIMT 直访 GM](../../../../runbooks/performance/random_gather_per_element_dma_should_switch_to_simt_direct_gm.md)（`related`）：快速入门给出一维 SIMT Gather 的 Device、Host、编译和运行骨架，focal 则把该机制扩展到随机多维逐轴地址解码与性能 A/B；可作为最小实现起点。
- [AiCoreSimtProgrammingOverview](../../../programming_guide/programming_model/ai_core_simt_programming/overview.md)（`same_topic`）：Gather算子快速入门 与《AiCoreSimtProgrammingOverview》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [MemoryAccessMerge](../../../operator_practice/simt_operator_optimization/memory_access/memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《Gather算子快速入门》提供“本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [基础知识（SIMT算子实现）](../../../operator_practice/simt_operator_impl/basics.md)（`same_topic`）：Gather算子快速入门 与《基础知识（SIMT算子实现）》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [异构系统与编程模型](../heterogeneous_system_and_programming_model.md)（`same_topic`）：Gather算子快速入门 与《异构系统与编程模型》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [算子实现（SIMT算子实现）](../../../operator_practice/simt_operator_impl/operator_impl.md)（`same_topic`）：Gather算子快速入门 与《算子实现（SIMT算子实现）》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [编程示例（AI Core SIMT编程）](../../../programming_guide/programming_model/ai_core_simt_programming/programming_examples.md)（`same_topic`）：Gather算子快速入门 与《编程示例（AI Core SIMT编程）》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
<!-- cannbot:related:end -->
