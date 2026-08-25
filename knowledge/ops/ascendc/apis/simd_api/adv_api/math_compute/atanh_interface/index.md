# Atanh接口

- [Atanh](atanh.md)：按元素做反双曲正切函数计算，输入值域需在指定区间内
- [Atanh接口](atanh_interface.md)：提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。
- [GetAtanhMaxMinTmpSize](get_atanh_max_min_tmp_size.md)：在host侧获取Atanh接口预留临时空间的最大和最小值，用于Tiling参数选择
- [GetAtanhTmpBufferFactorSize](get_atanh_tmp_buffer_factor_size.md)：获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
