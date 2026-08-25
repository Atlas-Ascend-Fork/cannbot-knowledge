# 矩阵计算

- [矩阵计算](cube_compute.md)：汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。
- [获取Matmul计算所需空间](get_matmul_compute_space/index.md)：BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。
- [Matmul Kernel侧接口](matmul_kernel/index.md)：获取Iterate接口异步计算的结果矩阵。该接口功能已被GetTensorC覆盖，建议直接使用GetTensorC异步接口。
- [Matmul Tiling类](matmul_tiling/index.md)：设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。
