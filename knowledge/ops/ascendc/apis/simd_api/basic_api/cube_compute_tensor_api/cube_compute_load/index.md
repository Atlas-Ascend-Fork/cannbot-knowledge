# 矩阵计算的搬入

- [CopyGmToL1](copy_gm_to_l1.md)：通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入。
- [CopyL1ToBiasTable](copy_l1_to_bias_table.md)：通过Tensor API的Copy接口将L1 Buffer中的bias数据搬运到BiasTable Buffer，作为Mmad计算的bias输入。
- [CopyL1ToFixpipe](copy_l1_to_fixpipe.md)：通过Tensor API的Copy接口将L1 Buffer中的量化数据搬运到Fixpipe Buffer，用于L0C输出时随路量化。
- [CopyL1ToL0A](copy_l1_to_l0_a.md)：通过Tensor API的Copy接口将L1 Buffer中的左矩阵数据搬运到L0A Buffer，支持转置搬运和Img2Col卷积展开。
- [CopyL1ToL0B](copy_l1_to_l0_b.md)：通过Tensor API的Copy接口将L1 Buffer中的右矩阵数据搬运到L0B Buffer，支持非转置和转置搬运。
- [CopyL1ToL0ScaleA](copy_l1_to_l0_scale_a.md)：通过Tensor API的Copy接口将L1 Buffer中的左矩阵缩放数据搬运到L0ScaleA Buffer，数据类型固定为fp8_e8m0_t。
- [CopyL1ToL0ScaleB](copy_l1_to_l0_scale_b.md)：通过Tensor API的Copy接口将L1 Buffer中的右矩阵缩放数据搬运到L0ScaleB Buffer，数据类型固定为fp8_e8m0_t。
- [矩阵计算的搬入](cube_compute_load.md)：矩阵计算 TensorAPI 搬入接口集，涵盖 GM 到 L1、L1 到 L0A/L0B 的 Copy 接口及 Buffer 内存结构说明。
- [矩阵计算的搬入总体说明](overall_description.md)：矩阵计算的搬入接口主要实现Global Memory到L1 Buffer和L1 Buffer到L0A Buffer/L0B Buffer/L0ScaleA Buffer/L0ScaleB Buffer/BiasTable Buffer/Fixpipe Buffer的数据高效传输。
