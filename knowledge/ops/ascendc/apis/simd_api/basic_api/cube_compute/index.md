# cube compute

- [矩阵计算分形介绍](cube_compute_fractal_intro/index.md)：针对Ascend 950PR/Ascend 950DT产品：
- [矩阵计算的搬入](cube_compute_load/index.md)：将矢量数据广播到矩阵中，每个数据块中的每16个元素会被连续复制16次；当前支持的数据传输通路：Unified Buffer-\>L0C Buffer（VECIN/VECCALC/VECOUT-\>CO1）。 图1 功能示例 !
- [矩阵计算（ISASI）](cube_compute_overview.md)：AscendC 矩阵计算 ISASI 接口总览，涵盖搬入、Mmad 计算、搬出及辅助配置与关键特性说明。
- [矩阵计算的搬出](cube_compute_store/index.md)：矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。
- [矩阵搬入辅助配置接口](cube_load_aux_config/index.md)：矩阵搬入辅助配置接口集，包含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataPaddingValue 等。
- [矩阵搬出寄存器配置说明](cube_store_aux_config/index.md)：本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。
- [矩阵搬出关键特性说明](cube_store_key_features/index.md)：矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。
- [矩阵计算（ISASI）](mmad_compute/index.md)：该接口废弃，并将在后续版本移除，请不要使用该接口。 计算给定输入张量和权重张量的2-D卷积，输出结果张量。Conv2D卷积层多用于图像识别，使用过滤器提取图像中的特征。
- [Mmad辅助配置说明](mmad_compute_aux_config/index.md)：Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。
- [Mmad计算关键特性说明](mmad_compute_key_features/index.md)：Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
- [概述](overview/index.md)：Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：
