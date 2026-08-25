# 矩阵计算（TensorAPI，试验特性）

- [矩阵计算分形介绍](cube_compute_fractal_intro/index.md)：矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。
- [矩阵计算的搬入](cube_compute_load/index.md)：通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入。
- [矩阵计算的搬出](cube_compute_store/index.md)：将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。
- [矩阵计算（TensorAPI，试验特性）](cube_compute_tensor_api.md)：AscendC 矩阵计算 TensorAPI（试验特性）接口总览，涵盖搬入、Mmad 计算、搬出及关键特性说明。
- [矩阵搬出关键特性说明](cube_store_key_features/index.md)：L0C Buffer到GM或UB搬运在矩阵最外层增加Batch维度的能力，用于一次完成多块矩阵计算结果的搬运。
- [mmad compute](mmad_compute/index.md)：完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。
- [Mmad计算辅助配置接口](mmad_compute_aux_config/index.md)：Mmad计算辅助配置接口列表如下：
- [Mmad计算关键特性说明](mmad_compute_key_features/index.md)：GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
- [概述](overview/index.md)：TensorAPI 矩阵计算概述，介绍矩阵计算单元与搬入、Mmad、搬出的基础计算流程。
