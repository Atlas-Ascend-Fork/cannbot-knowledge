# programming guide

- [高级编程](advanced_programming/index.md)：AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
- [appendix](appendix/index.md)：>本章节介绍的基于样例工程完成Kernel直调的方式，后续不再演进。推荐开发者直接使用命令行或者编写Cmake文件进行编译，详细内容请参考AI Core SIMD编译。
- [编译与运行](compilation_and_execution/index.md)：当开发者完成一个Kernel核函数的编写后，需要通过特定的下发/启动语法将其提交到指定的Stream（计算流）上执行。例如：
- [调试调优](debug_and_tuning/index.md)：介绍Ascend C算子调试与调优整体方案，涵盖CPU域孪生调试、NPU域上板调试及性能调优工具。
- [本文档组织结构（编程指南）](document_structure.md)：本指南为AscendC算子开发综合技术手册，系统涵盖SIMD/SIMT编程模型、语言扩展特性、C++类库API、编译运行机制、调试调优及高级编程等核心技术。文档兼顾入门学习与深度实践，适配不同层级研发人员。入门开发者可依托本指南完成技术体系搭建，资深算子工程师亦可借此深化技术能力，充分挖掘昇腾AI处理器硬件算力，高质量完成自定义算子的开发与性能优化。
- [语言扩展层](language_extension/index.md)：如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
- [类库API](library_api/index.md)：>本章提供编程API的概述。具体API参考见Ascend C API。
- [编程模型](programming_model/index.md)：AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力，可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算，通常作为AI Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。AI CPU的运行环境为基础的Linux环境，编程时可使用libc库，C++标准库，STL模板库等。其硬件架构图如下所示：
