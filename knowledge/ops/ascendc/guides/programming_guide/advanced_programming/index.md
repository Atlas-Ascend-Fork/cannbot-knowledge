# 高级编程

- [aclnn operator development](aclnn_operator_development/index.md)：本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
- [高级AI-Core编程模型](advanced_ai_core_programming_model/index.md)：Ascend C支持SIMD与SIMT混合编程，实现向量级并行与线程级并行的高效协同。AI Core包含AIC和AIV，其中AIV核支持SIMT、SIMD两种工作模式，因此可以实现AIV内SIMD与SIMT的混合编程，也支持AIV的SIMT与AIC的SIMD融合编程，整体硬件架构如下图所示：
- [ai framework adaptation](ai_framework_adaptation/index.md)：本章节内容介绍AI框架调用自定义算子的方法。如下图所示，Pytorch支持单算子和图模式两种，TensorFlow仅支持图模式。
- [AOT编译优化（高级编程）](aot_compilation_optimization.md)：AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
- [硬件实现](hardware_implementation/index.md)：如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型；对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参考中很多内容都以本章为基础进行介绍。
- [内存模型](memory_model/index.md)：本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性。
- [operator graph development](operator_graph_development/index.md)：该开发流程以工程化算子开发为基础，除了需要提供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件。本节仅提供算子入图代码文件的开发指导。
- [SIMT协作组简介（高级编程）](simt_cooperative_groups.md)：协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
- [super kernel](super_kernel/index.md)：对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。
