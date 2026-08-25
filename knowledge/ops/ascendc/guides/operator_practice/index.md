# operator practice

- [优秀实践（最佳实践）](best_practices/index.md)：本案例中的算子FlashAttentionScoreGrad，用于训练场景下计算注意力的反向输出，即FlashAttentionScore算子的反向计算。
- [本文档组织结构（算子实践）](document_structure.md)：本文档主要用于指导开发者基于Ascend C编程语言在昇腾AI处理器上开发高性能的算子。在阅读此文档时，需要开发者具备如下能力：
- [功能调试](functional_debug/index.md)：性能优化的基础是算子运行得到正确的计算结果。评判计算结果正确性需要有一定的评判标准，即使用已知的正确的输出和实际结果进行比较。优化过程中，每次迭代修改后，都需要验证性能优化的新结果是否满足精度评判标准。
- [异构计算（算子实践）](heterogeneous_computing.md)：使用Ascend C进行编程时，会涉及到在两个不同的平台（Host、Device）上开发代码。本章简单介绍Host、Device之间的差异，便于开发者宏观地了解这个异构系统；同时给出算子相关的数据流，结合异构架构的特点，开发者可以进一步了解应该如何合理安排算子代码的执行位置，便于得到更好的性能。
- [性能分析](performance_analysis/index.md)：理论性能为算子实际性能的理想目标。不同的硬件平台的硬件规格各异，理论性能可以帮助我们了解硬件的潜能，从而设定性能优化的目标。
- [simd operator impl](simd_operator_impl/index.md)：>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。
- [SIMD算子性能优化](simd_operator_optimization/index.md)：【描述】算子中进行带bias的矩阵乘计算时，可将bias数据搬运至Bias Table Buffer（C2）上，调用一次Mmad接口实现矩阵乘加bias的计算，或者直接调用Matmul高阶API完成功能。相比于先将矩阵乘的结果从L0C...
- [SIMD与SIMT混合算子实现](simd_simt_hybrid_operator_impl/index.md)：本节内容为使用Reg矢量计算API和SIMT API进行SIMD与SIMT混合编程的指导。
- [SIMD与SIMT混合算子性能优化](simd_simt_hybrid_optimization/index.md)：>该性能优化建议适用于如下型号：
- [simt operator impl](simt_operator_impl/index.md)：本节内容为使用SIMT API进行SIMT编程的指导。
- [SIMT算子性能优化](simt_operator_optimization/index.md)：同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。
- [典型算子实践案例（典型算子案例）](typical_operator_cases/index.md)：本节在中级性能优化的基础上，介绍Add算子的高阶极限打磨方法。
