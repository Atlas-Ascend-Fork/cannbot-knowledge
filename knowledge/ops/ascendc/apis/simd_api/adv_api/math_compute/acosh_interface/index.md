# Acosh接口

- [Acosh](acosh.md)：按元素做双曲反余弦函数计算，输入值域需在1到65504范围内
- [Acosh接口](acosh_interface.md)：提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。
- [GetAcoshMaxMinTmpSize](get_acosh_max_min_tmp_size.md)：在host侧获取Acosh接口预留临时空间的最大和最小值，用于Tiling参数选择
- [GetAcoshTmpBufferFactorSize](get_acosh_tmp_buffer_factor_size.md)：获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
