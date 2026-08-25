# Axpy接口

- [Axpy](axpy.md)：源操作数各元素与标量求积后加到目的操作数对应元素，通过Muls和Add组合提升精度
- [Axpy接口](axpy_interface.md)：提供Axpy(y=a*x+y)计算接口及其Tiling临时空间大小查询接口，包含Axpy、GetAxpyMaxMinTmpSize等。
- [GetAxpyMaxMinTmpSize](get_axpy_max_min_tmp_size.md)：在host侧获取Axpy接口申请临时空间的最大和最小值，用于Tiling参数选择
- [GetAxpyTmpBufferFactorSize](get_axpy_tmp_buffer_factor_size.md)：获取Axpy接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
