# AI-Core-SIMD编程

- [抽象硬件架构（AI Core SIMD编程）](abstract_hardware_architecture.md)：AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。
- [c pointer programming](c_pointer_programming/index.md)：C语言编程是Ascend C SIMD编程的底层核心接口，直接映射NPU硬件指令，支持精细化控制向量、矩阵和存储等硬件资源。
- [cpp tensor programming](cpp_tensor_programming/index.md)：Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。
- [核函数（AI Core SIMD编程）](kernel_function.md)：核函数（Kernel Function）是在设备侧并行执行的C/C++函数。它由主机端代码调用，调用时被实例化为多份并行副本，分别调度到多个AI Core上运行（每个AI Core被抽象为一个Block）。这些Block利用AI Core的计算能力，协同完成某一算子的计算。
- [AI Core SIMD编程模型概述](overview.md)：SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。
- [tpipe tque programming](tpipe_tque_programming/index.md)：上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。
