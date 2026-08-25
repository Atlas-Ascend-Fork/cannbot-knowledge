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

<!-- cannbot:related:start -->
## 相关

- [LocalMemAllocator](../../../../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《LocalMemAllocator》说明LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [Mmad](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [普通矩阵计算流程（概述）](../../../../../apis/simd_api/basic_api/cube_compute/overview/cube_compute_flow.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《普通矩阵计算流程（概述）》说明Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [矩阵计算](../../../../../apis/simd_api/adv_api/cube_compute/cube_compute.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算》说明汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [矩阵计算分形介绍](../../../../../apis/simd_api/basic_api/cube_compute/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算分形介绍》说明矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [矩阵计算单元（概述）](../../../../../apis/simd_api/basic_api/cube_compute/overview/cube_compute_unit.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算单元（概述）》说明Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C Buffer则用于存储初始化累加值和矩阵计算结果。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [CppTensorProgrammingOverview](cpp_tensor_programming_overview.md)（`related`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《CppTensorProgrammingOverview》说明Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`related`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《抽象硬件架构（AI Core SIMD编程）》说明AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [静态Tensor编程](static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [Cube矩阵计算编程](../c_pointer_programming/cube_matrix_computation.md)（`same_topic`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《Cube矩阵计算编程》说明本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
<!-- cannbot:related:end -->
