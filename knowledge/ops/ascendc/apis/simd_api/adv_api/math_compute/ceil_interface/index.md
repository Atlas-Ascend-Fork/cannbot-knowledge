# Ceil接口

- [Ceil](ceil.md)：获取大于或等于输入值的最小整数，即向正无穷方向取整
- [Ceil接口](ceil_interface.md)：提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。
- [GetCeilMaxMinTmpSize](get_ceil_max_min_tmp_size.md)：在host侧获取Ceil接口预留临时空间的最大和最小值，用于Tiling参数选择
- [GetCeilTmpBufferFactorSize](get_ceil_tmp_buffer_factor_size.md)：获取Ceil接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
