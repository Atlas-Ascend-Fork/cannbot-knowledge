# BitwiseAnd接口

- [BitwiseAnd](bitwise_and.md)：逐比特对两个输入进行与操作。 !
- [BitwiseAnd接口](bitwise_and_interface.md)：提供BitwiseAnd按位与运算接口及其Tiling临时空间大小查询接口，包含BitwiseAnd、GetBitwiseAndMaxMinTmpSize等。
- [GetBitwiseAndMaxMinTmpSize](get_bitwise_and_max_min_tmp_size.md)：用于在Host侧获取BitwiseAnd接口所需的最大和最小临时空间大小，作为Tiling参数传递到Kernel侧使用。
- [GetBitwiseAndTmpBufferFactorSize](get_bitwise_and_tmp_buffer_factor_size.md)：获取maxLivedNodeCount和extraBuf，在固定空间大小下推算BitwiseAnd算子单次最大计算元素数量。
