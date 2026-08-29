---
type: Guide
title: MemoryVectorComputation
description: 基于Unified Buffer的矢量计算编程方式，是Ascend C最基础、最通用的矢量编程接口，支持数据搬入、计算、搬出三步流程。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/memory_vector_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Memory矢量计算编程

本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于Unified Buffer（以下简称UB）的矢量计算代码，该能力是Ascend C最基础、最通用的矢量编程方式。这种基于UB内存的编程方式被称为Memory矢量计算编程。NPU架构版本2201产品支持完整的Memory矢量计算UB直接编程能力；而NPU架构版本3510虽也支持UB操作，但推荐使用Reg矢量计算编程以获得更高性能。
## Memory矢量编程的基本步骤
Memory矢量计算的数据流为：数据搬入 → 计算 → 数据搬出。当我们描述一个常见的Vector矢量计算时，需要执行以下三个步骤：
1. 通过DMA将数据从Global Memory搬入到Local Memory
2. 进行矢量计算
3. 通过DMA将数据从Local Memory搬出到Global Memory
## Memory矢量计算内存管理
Memory矢量编程的核心是基于Local Memory（UB）完成矢量计算，要求开发者先将输入数据从Global Memory（以下简称GM）搬入UB，再通过Vector计算指令执行运算。UB的管理依赖LocalTensor对象实现，开发者可通过LocalMemAllocator分配器申请UB空间，为后续矢量计算提供存储载体。
### 基础Tensor(不带Layout)定义
通过LocalMemAllocator内存分配器创建，用户可指定物理存储位置和内存大小。
## Memory数据搬运
GM与UB之间的数据搬运提供了多样化的接口，支持丰富的数据搬运场景。为实现高效的Vector计算，系统支持将数据从GM搬运至UB，供Vector计算单元进行向量计算。计算完成后，再将结果从UB搬回GM，完成数据闭环。
开发者通过灵活配置DataCopyParams参数，精确控制数据块数量、地址长度及间隔等关键属性，实现连续和非连续数据搬运（高维切分数据搬运），充分释放硬件的数据搬运与计算协同能力，提升向量算子的执行效率。
数据通路：模式：接口：适用场景
GM→UB：连续搬运：DataCopy(dst, src, count)：一维连续数据搬运
GM→UB：高维切分：DataCopy(dst, src, dataCopyParams)：多块非连续数据，可配置块数和间隔
GM→UB：非对齐搬运：DataCopyPad(dst, src, dataCopyExtParams, padParams)：地址非32B对齐，支持自定义填充
UB→GM：连续搬运：DataCopy(dst, src, count)：一维连续数据搬运
UB→GM：高维切分：DataCopy(dst, src, dataCopyParams)：多块非连续数据，可配置块数和间隔
UB→GM：非对齐搬运：DataCopyPad(dst, src, dataCopyExtParams)：地址非32B对齐
根据上述矢量搬运能力的描述，开发者可以根据不同的场景选择合适的接口进行处理。
