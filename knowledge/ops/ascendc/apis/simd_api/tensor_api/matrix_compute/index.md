# 矩阵计算（Tensor API）

- [矩阵计算的搬入](cube_compute_load/index.md)：头文件路径为：tensor_api/tensor.h。
- [矩阵计算的搬出](cube_compute_store/index.md)：头文件路径为：tensor_api/tensor.h。
- [矩阵搬出关键特性说明](cube_store_key_features/index.md)：源张量为NZ格式，目的张量支持ND、DN或NZ格式。用户只需要在构造layout时传入Batch参数，copy调用形式与非batch模式保持一致。
- [矩阵计算（Tensor API）](matrix_compute.md)：矩阵计算由数据搬入、mmad计算和结果搬出组成。各阶段通过Tensor的存储位置和Layout选择对应Arch通路，通过Atom配置Trait及运行时Params。
- [矩阵计算](mmad_compute/index.md)：头文件路径为：tensor_api/tensor.h。
- [mmad计算辅助配置接口](mmad_compute_aux_config.md)：mmad计算辅助配置接口列表如下：
- [mmad计算关键特性说明](mmad_compute_key_features/index.md)：GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
- [概述](overview.md)：矩阵计算单元的详细描述请参考LINK。
