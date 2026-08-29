---
type: Guide
title: Cube矩阵计算编程
description: 本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cube矩阵计算编程

本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。
AI Core包含Vector计算单元（部署于AIV核）和Cube计算单元（部署于AIC核）。Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储初始累加值及矩阵计算结果。
## 矩阵编程的基本步骤
Cube矩阵计算的基本步骤为：数据搬入 → 数据加载 → 计算 → 数据搬出。当我们描述一个常见的Cube矩阵计算时，需要执行以下四个步骤：
1. 通过DMA将数据从GM搬入到Local Memory(L1 Buffer)
2. 通过数据加载将L1 Buffer搬入到L0A Buffer & L0B Buffer
3. 进行矩阵计算，计算结果存储在L0C Buffer中
4. 通过DMA将数据从L0C Buffer搬出到GM
## 矩阵计算内存管理
### 矩阵计算内存申请
矩阵计算编程主要通过L0A/L0B/L0C Buffer进行矩阵计算。开发者需将输入数据从Global Memory（以下简称GM）搬入L1 Buffer，再从L1 Buffer搬入L0A/L0B Buffer，最终通过Cube计算指令完成计算。L1 Buffer与L0A/L0B/L0C Buffer均通过LocalTensor对象进行管理，开发者可通过LocalMemAllocator分配器申请矩阵计算所需的内存空间。
### 矩阵计算内存布局
矩阵计算单元采用分块计算逻辑，其中16×16是矩阵计算单元分形的基本粒度（对于half数据类型；int8类型为16×32或32×16；fp32类型分形为16×8），硬件可以并行处理多个矩阵计算单元。在传统的线性存储布局（如行主序或列主序）中，数据按行或列连续存放。当需要读取一个16×16的矩形数据块时，若直接从内存中获取，则需访问不连续的多个内存地址以逐行“收集”数据，这种非连续访问会导致内存效率显著下降。
为解决上述问题，引入了矩阵分形存储格式。该格式通过软件层对数据进行重排，使每个16×16计算块在物理内存中连续存放。硬件仅需发起一次连续读取，即可将整个数据块加载至片上寄存器，避免了多地址寻址开销，从而大幅提升矩阵计算单元的数据吞吐率。对于half数据类型，16×16是矩阵计算单元的基本分形粒度，当前支持Cube计算的产品型号包括NPU架构版本2201和NPU架构版本3510。
昇腾AI处理器的矩阵计算单元为追求极高的数据吞吐率与计算密度，采用了专有的硬件架构设计。与通用CPU常用的连续线性存储不同，该单元要求输入输出数据必须符合特定的分形存储格式。在使用Ascend C的Mmad类接口进行算子开发时，深入理解这些数据格式对于实现正确的数据搬运、分块及性能优化至关重要。
为便于理解与记忆，文档采用“大Y小x”的直观命名法：
- 大Y（Z/N）：表示分形矩阵之间的排列顺序（Z为行主序，N为列主序）。
- 小x（z/n）：表示分形矩阵内部元素的排列顺序（z为行主序，n为列主序）。
### 关键分形格式详解
矩阵分形存储格式是对多维Tensor在内存中数据排布格式的描述。
