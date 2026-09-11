# 高阶API

- [激活函数](activation_functions/index.md)：采用GELU作为激活函数的GLU变体，按元素对两源Tensor计算GeGLU结果
- [卷积计算](convolution_compute/index.md)：Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。
- [矩阵计算](cube_compute/index.md)：BatchMatmul Tiling调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。
- [数据过滤](data_filter/index.md)：根据MaskTensor对SrcTensor进行过滤，支持字节模式和比特模式两种过滤方式
- [数据结构](data_structures/index.md)：汇总高阶API在Host侧Tiling接口中使用的Ascend C公共类型，包含TensorShape、TensorDataType等数据结构定义。
- [HCCL通信类](hccl_communication/index.md)：获取指定Index通信域的context（消息区）地址。
- [索引计算](index_compute/index.md)：给定起始值，等差值和长度，返回一个等差数列。
- [数学计算](math_compute/index.md)：下面的样例展示了数学库kernel侧API和Tiling API GetXxxMaxMinTmpSize的配套使用方法，具体流程如下：
- [归一化操作](normalization/index.md)：对每一层输入做规范化处理，在batch维度上计算均值和方差进行归一化，再通过缩放和平移参数调整分布，加速训练并提升泛化能力。
- [量化操作](quantization/index.md)：按元素做伪量化计算，将int8_t等低精度数据类型伪量化为half等高精度数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种量化策略，最多支持二维输入。
- [随机函数](random_functions/index.md)：基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。
- [归约操作](reduction_operations/index.md)：在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择。
- [排序操作](sort_operations/index.md)：对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。
- [张量变换](tensor_transform/index.md)：将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。
