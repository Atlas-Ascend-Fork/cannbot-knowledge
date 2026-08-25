# Cos接口

- [Cos](cos.md)：按元素做余弦运算，支持多项式逼近和周期约减两种算法配置
- [Cos接口](cos_interface.md)：提供Cos余弦计算接口及其Tiling临时空间大小查询接口，包含Cos、GetCosMaxMinTmpSize等。
- [GetCosMaxMinTmpSize](get_cos_max_min_tmp_size.md)：在host侧获取Cos接口预留临时空间的最大和最小值，用于Tiling参数选择
- [GetCosTmpBufferFactorSize](get_cos_tmp_buffer_factor_size.md)：获取Cos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
