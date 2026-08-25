# programming guide

- [高级编程](advanced_programming/index.md)：本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
- [appendix](appendix/index.md)：动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解析输入数据方面有差异：核函数的入参采用ListTensorDe...
- [编译与运行（编译与执行）](compilation_and_execution/index.md)：当开发者完成一个Kernel核函数的编写后，需要通过特定的下发/启动语法将其提交到指定的Stream（计算流）上执行。例如：
- [调试调优（调试与调优）](debug_and_tuning/index.md)：介绍Ascend C算子调试与调优整体方案，涵盖CPU域孪生调试、NPU域上板调试及性能调优工具。
- [本文档组织结构（编程指南）](document_structure.md)：本指南为AscendC算子开发综合技术手册，系统涵盖SIMD/SIMT编程模型、语言扩展特性、C++类库API、编译运行机制、调试调优及高级编程等核心技术。文档兼顾入门学习与深度实践，适配不同层级研发人员。入门开发者可依托本指南完成技术体系搭建，资深算子工程师亦可借此深化技术能力，充分挖掘昇腾...
- [语言扩展层](language_extension/index.md)：如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
- [类库API](library_api/index.md)：高阶API基于单核对常见算法进行抽象和封装，实现了一些常用的计算算法，旨在提高编程开发效率。高阶API一般通过调用多种基础API实现。高阶API包括数学计算、矩阵计算、激活函数等API。
- [编程模型](programming_model/index.md)：AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开...
