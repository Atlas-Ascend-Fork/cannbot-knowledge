# 矩阵计算的搬出

- [Copy](copy_l0_c_to_gm.md)：将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。
- [Copy](copy_l0_c_to_ub.md)：将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。
- [矩阵计算的搬出](cube_compute_store.md)：矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。
- [矩阵计算的搬出总体说明](overall_description.md)：矩阵计算的搬出接口主要实现L0C Buffer与Global Memory、Unified Buffer之间的数据高效传输。
