# Acos接口

- [Acos](acos.md)：按元素做反余弦函数计算，输入值域需在-1到1范围内
- [Acos接口](acos_interface.md)：提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等。
- [GetAcosMaxMinTmpSize](get_acos_max_min_tmp_size.md)：在host侧获取Acos接口预留临时空间的最大和最小值，用于Tiling参数选择
- [GetAcosTmpBufferFactorSize](get_acos_tmp_buffer_factor_size.md)：获取Acos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
