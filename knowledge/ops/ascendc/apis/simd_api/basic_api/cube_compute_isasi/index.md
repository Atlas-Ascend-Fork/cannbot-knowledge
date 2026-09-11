# 矩阵计算（ISASI）

- [矩阵计算分形介绍](cube_compute_fractal_intro/index.md)：针对Ascend 950PR/Ascend 950DT产品：
- [矩阵计算的搬入](cube_compute_load/index.md)：将矢量数据广播到矩阵中，每个数据块中的每16个元素会被连续复制16次；当前支持的数据传输通路：Unified Buffer-\>L0C Buffer（VECIN/VECCALC/VECOUT-\>CO1）。 图1 功能示例 !
- [矩阵计算的搬出](cube_compute_store/index.md)：将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。
- [矩阵搬入辅助配置接口](cube_load_aux_config/index.md)：将L1 Buffer/L0A Buffer/L0B Buffer上的LocalTensor初始化为指定数值，通过InitConstValueParams配置迭代次数、数据块个数和填充值。
- [矩阵搬出寄存器配置说明](cube_store_aux_config/index.md)：本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。
- [矩阵搬出关键特性说明](cube_store_key_features/index.md)：矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。
- [矩阵计算](mmad_compute/index.md)：该接口废弃，并将在后续版本移除，请不要使用该接口。 计算给定输入张量和权重张量的2-D卷积，输出结果张量。Conv2D卷积层多用于图像识别，使用过滤器提取图像中的特征。
- [Mmad辅助配置说明](mmad_compute_aux_config/index.md)：用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。
- [Mmad计算关键特性说明](mmad_compute_key_features/index.md)：Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
- [概述](overview/index.md)：Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：
