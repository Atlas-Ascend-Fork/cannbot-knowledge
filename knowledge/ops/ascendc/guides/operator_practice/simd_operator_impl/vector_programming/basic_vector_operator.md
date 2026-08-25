---
type: Guide
title: 基础矢量算子
description: 基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/basic_vector_operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础矢量算子

基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。
-   算子分析：分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要调用的Ascend C接口。
-   核函数定义：定义Ascend C算子入口函数。
-   根据矢量编程范式实现算子类：完成核函数的内部实现，包括3个基本任务：CopyIn，Compute，CopyOut。
下文以输入为half数据类型且shape的最后一维为32Bytes对齐、在单核上运行的、一次完成计算的Add算子为例，对上述步骤进行详细介绍。
## 算子分析
算子分析具体步骤如下：
1.  明确算子的数学表达式及计算逻辑。
Add算子的数学表达式为：
计算逻辑是：Ascend C提供的矢量计算接口的操作元素都为LocalTensor，输入数据需要先从外部存储（Global Memory）搬运进片上存储（Unified Buffer），然后使用计算接口完成两个输入参数相加，得到最终结果，再搬出到外部存储上。Ascend C  Add算子的计算逻辑如下图所示。
2.  明确输入和输出。
-   Add算子有两个输入：x与y；输出为z。
-   本样例中算子的输入支持的数据类型为half（float16），算子输出的数据类型与输入的数据类型相同。
-   算子输入支持的shape为（1，2048），输出shape与输入shape相同。
-   算子输入支持的format为：ND。
3.  确定核函数名称和参数。
-   您可以自定义核函数名称，本样例中核函数命名为vec_add_custom。
-   根据对算子输入输出的分析，确定核函数有3个参数x，y，z；x，y为输入在Global Memory上的内存地址，z为输出在Global Memory上的内存地址。
4.  确定算子实现所需接口。
-   实现涉及外部存储和内部存储间的数据搬运，查看Ascend C  API参考中的数据搬运接口，需要使用DataCopy来实现数据搬运。
-   本样例只涉及矢量计算的加法操作，查看Ascend C  API参考中的矢量计算接口，初步分析可使用基础算术Add接口Add实现x+y。
-   使用Queue队列管理计算中使用的Tensor数据结构，具体使用EnQue、DeQue等接口。
通过以上分析，得到Ascend C  Add算子的设计规格如下：
-   算子类型（OpType）：Add
-   算子输入输出：
Add算子输入输出规格
-   核函数名称：vec_add_custom
-   使用的主要接口：
-   DataCopy：数据搬移接口
-   Add：矢量基础算术接口
-   EnQue、DeQue等接口：Queue队列管理接口
-   算子实现文件名称：vector_add.asc
## 核函数定义
根据核函数中介绍的规则进行核函数的定义。

<!-- cannbot:related:start -->
## 相关

- [DeQue](../../../../apis/simd_api/basic_api/resource_management/t_que/de_que.md)（`explains`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《DeQue》说明将Tensor从队列中取出用于后续处理，支持non-inplace和inplace两种接口，可通过TQueBind指定源和目的位置。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [EnQue](../../../../apis/simd_api/basic_api/resource_management/t_que/en_que.md)（`explains`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《EnQue》说明将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](../../../../runbooks/compilation/datacopypad_copyin_32b_dma.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《DataCopyPad CopyIn 小输入 32B DMA 越界》说明DataCopyPad CopyIn 不论 DataCopyExtParams.blockLen 写多少，底层 DMA 引擎按 32 字节（1 DataBlock）粒度读 GM；当 Host 仅按有效元素数分配 < 32B 输入、SetGlobalBuffer(ptr,N) 只声明逻辑可读范围不扩大物理分配时，DMA 实读 32B 越过已映射内存 → device error 507035 / segfault。判别：小输入（有效元素 × sizeof(T) < 32B）+ SetGlobalBuffer N < ceil(32/sizeof(T)) + Host 分配未对齐到 32B。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [DoubleBuffer场景](double_buffer_scenario.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《DoubleBuffer场景》说明因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [SIMD算子实现主块均分](multi_core_tiling/main_block_even_split.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [SIMD算子实现尾块均分](multi_core_tiling/tail_block_even_split.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现尾块均分》说明该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [TBuf的使用](tbuf_usage.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《TBuf的使用》说明在大多数算子开发时，核函数计算过程需要使用临时内存来存储运算的中间结果，这些中间结果以临时变量表示，临时变量占用的内存可以使用TBuf数据结构来管理，具体介绍请参考TBuf。下文将以输入的数据类型为bfloat16_t、在单核上运行的Add算子为例，介绍TBuf的使用方式。本文中介绍的算子完整代码请参见使用临时内存的Add算子样例。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [TailCoreSplit](multi_core_tiling/tail_core_split.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《TailCoreSplit》说明主块均分后剩余数据无法以DataBlock均匀分配到每个核时，将额外DataBlock分配给前几个整核，其余为尾核，分别处理不同数据量。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [TailCoreTailBlockSplit](multi_core_tiling/tail_core_tail_block_split.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《TailCoreTailBlockSplit》说明主块均分后剩余DataBlock无法均分到每个核时，整核和尾核都包含尾块，整核比尾核多处理一个DataBlock，需分别记录Tiling参数。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [中级性能优化](../../typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《中级性能优化》说明本节在入门功能落地的基础上，介绍Add算子的中级性能优化方法。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [入门功能落地](../../typical_operator_cases/simd_operator_impl/add_vector_operator/getting_started.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《入门功能落地》说明本节以Add（向量加法）算子为例，介绍基于Ascend C编程模型实现向量算子的基本方法，帮助开发者快速入门SIMD算子开发。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [非对齐场景](unaligned_scenario.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《非对齐场景》说明本节介绍非32字节对齐数据的更多处理方式，包括数据搬入、计算和搬出的处理。用户在实际算子开发中，可以参考如下方案介绍和算子样例灵活地处理非对齐场景。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [SIMD算子实现概述](overview.md)（`same_topic`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现概述》说明本节将以Add算子为例，带您快速构建Ascend C矢量算子程序，并学习矢量算子开发的典型场景以及处理方式。涉及的场景包括：。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
<!-- cannbot:related:end -->
