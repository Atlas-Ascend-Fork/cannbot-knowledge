# 编程模型

- [AI-Core-SIMD编程](ai_core_simd_programming/index.md)：AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。
- [AI-Core-SIMT编程](ai_core_simt_programming/index.md)：AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂算子和不规则控制流的开发，缓解包含分支的发散计算并控制程序复杂度，从而提高硬件利用率和能效。
- [AI CPU编程（编程模型）](ai_cpu_programming.md)：AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力，可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算，通常作为AI Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。AI CPU的运行环境为基础的Linux环境，编程时可使用libc库，C++标准库，STL模板库等。其硬件架构图如下所示：
- [异构系统（编程模型）](heterogeneous_system.md)：一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory。
- [编程模型概述](programming_model_overview.md)：介绍Ascend C编程模型，涵盖SIMD与SIMT并行执行模型、AI Core硬件基础及编程路径选择。
