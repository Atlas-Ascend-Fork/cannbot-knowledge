# simd operator impl

- [add vector operator](add_vector_operator/index.md)：本节在中级性能优化的基础上，介绍Add算子的高阶极限打磨方法。
- [gelu reg vector operator](gelu_reg_vector_operator/index.md)：本节在中级性能优化的基础上，介绍GELU算子的高阶极限打磨方法。
- [matmul leakyrelu fusion operator](matmul_leakyrelu_fusion_operator/index.md)：本节在中级性能优化的基础上，介绍Matmul融合算子的高阶极限打磨方法。
- [matmul matrix operator](matmul_matrix_operator/index.md)：本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag...
