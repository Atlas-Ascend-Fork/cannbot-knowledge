# LogicalAnd接口

- [GetLogicalAndMaxMinTmpSize](get_logical_and_max_min_tmp_size.md)：在host侧获取LogicalAnd接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
- [GetLogicalAndTmpBufferFactorSize](get_logical_and_tmp_buffer_factor_size.md)：获取LogicalAnd接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
- [LogicalAnd](logical_and.md)：按元素进行与操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
- [LogicalAnd接口](logical_and_interface.md)：按元素进行逻辑与操作，非零视为True、零视为False，并提供临时空间大小获取接口。
