---
type: Guide
title: ThreadArchitecture
description: SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/thread_architecture.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 线程架构

SIMT编程模型采用分层的抽象线程组织结构，从顶层到底层依次为：Grid（线程块网格）、Thread Block（线程块）和Thread（线程）。这种层次化的设计使得开发者可以方便地将并行计算问题映射到硬件资源上。同时，每个层次中的维度均可由开发者根据算法与数据规模自定义配置。如下图所示，其中线程块是按照一维组织排布，每个线程块的索引为0-4； 线程块内的线程是按照二维组织排布，每个线程由坐标(threadIdx.x, threadIdx.y)唯一标识。
## 线程层次结构
Thread（线程）
线程是整个架构中的最小单元，每个线程独立完成计算任务，拥有独立的寄存器和栈空间。
Thread Block（线程块）
Thread Block由若干线程组成（最大2048个线程），使用内置变量blockDim表示一个线程块在各维度上的线程数量。Thread Block有以下特征：
-   同一Thread Block内的线程可以访问共享内存实现数据交互；
-   Thread Block内的线程可通过同步机制实现协作；
Grid（线程块网格）
Grid是SIMT线程层次结构的最顶层，由多个Thread Block组成。使用内置变量gridDim来表示Grid在各维度上的线程块数量，并有以下特征：
-   Grid的维度由用户的执行配置决定，核函数执行期间不可更改；
-   Grid中的所有线程块具有相同的尺寸和维度配置；
-   同一Grid中的线程块相互独立，按任意顺序执行；
-   基于SIMT编程模型的程序，在AIV核上执行多个结构相同的线程块，执行的总线程数等于gridDim.x*gridDim.y*gridDim.z*blockDim.x*blockDim.y*blockDim.z。
当前Grid中线程块总数不能超过65535。
线程索引
在SIMT线程架构下，每个线程都有唯一的标识，开发者可以通过内置变量获取线程的身份信息，从而确定每个线程负责处理的数据，相关内置变量如下表所示：
gridDim：Grid的维度大小。：dim3
实际上，每个线程块内的线程并无法同时并发执行，底层是通过Warp对线程块内的线程进行划分，在一个Thread Block内，所有线程按线性顺序被硬件自动划分为每32个线程一组的Warp，同一Warp内的所有线程执行同一条指令。Warp是SIMT架构中基本的调度和执行单位。Warp内的线程从相同的程序地址开始执行，拥有各自的指令地址计数器和寄存器状态，并且可以选择分支独立执行。基于Warp的划分机制，Thread Block的blockDim建议设置为32的整数倍，否则最后一个Warp将包含不足32个线程，导致该Warp内存在空闲线程通道，进而降低执行效率。
Warp内的线程虽然执行同一段代码，但在分支处可能进入不同的执行路径，这种情况称为分支发散（Warp Divergence）。控制流指令（if、switch、do、for、while）都可能会引起分支发散。

<!-- cannbot:related:start -->
## 相关

- [扩展语法内置变量](../../../../apis/simt_api/simt_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：内置变量是实现线程架构身份映射的实际接口，直接提供 gridDim、blockDim、blockIdx、threadIdx。
- [核函数配置](../../../../apis/simt_api/simt_programming_intro/extended_syntax/kernel_function_config.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《ThreadArchitecture》具体提供“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [编程模型](../../../../apis/simt_api/simt_programming_intro/programming_model.md)（`explains`）：SIMT API 模型定义 Grid/Block/Thread 内置维度，线程架构指南解释这些维度如何映射到 Warp 调度。
- [原子操作（AI Core SIMT编程）](atomic_operations.md)（`related`）：Thread/Block/Grid 的独立执行与共享范围决定哪些线程可能并发更新同一地址，是选择原子作用域的前提。
- [同一Warp内避免分支跳转](../../../operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《ThreadArchitecture》具体提供“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
- [编程示例（AI Core SIMT编程）](programming_examples.md)（`related`）：ThreadArchitecture说明SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [内存层级（AI Core SIMT编程）](memory_hierarchy.md)（`same_topic`）：焦点处理SIMT 内存层级与地址空间、同步可见性；ThreadArchitecture正文界定“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [抽象硬件架构（AI Core SIMT编程）](abstract_hardware_architecture.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“ThreadArchitecture”明确SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [核函数（AI Core SIMT编程）](kernel_function.md)（`same_topic`）：线程架构说明 block/thread/warp 的索引和执行范围，决定 kernel 内如何把全局数据映射到每个 SIMT 线程。
<!-- cannbot:related:end -->
