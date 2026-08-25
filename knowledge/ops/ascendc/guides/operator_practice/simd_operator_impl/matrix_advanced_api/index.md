# matrix advanced api

- [SIMD算子实现基础知识](basics.md)：>本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通过API参考确认接口支持的产品型号。
- [feature scenarios](feature_scenarios/index.md)：对稀疏矩阵B进行4:2稠密化后调用Matmul API完成矩阵乘，跳过零元素以减少内存占用和计算量。
- [算子实现](operator_impl.md)：介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。
