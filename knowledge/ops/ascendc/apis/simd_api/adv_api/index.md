# adv api

- [激活函数](activation_functions/index.md)：汇总Ascend C SIMD高阶API中各类激活函数接口，包括SoftMax、LogSoftMax、Gelu、SwiGLU、Silu、Swish、GeGLU、ReGlu、Sigmoid等。
- [卷积计算](convolution_compute/index.md)：提供Conv3D反向卷积滤波器梯度的Kernel侧接口，包含Init、SetInput、SetGradOutput、Iterate等方法及使用说明。
- [矩阵计算](cube_compute/index.md)：汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。
- [数据过滤](data_filter/index.md)：提供Ascend C SIMD高阶API中的数据过滤接口，包含Select、DropOut及其Tiling临时空间大小查询接口。
- [数据结构](data_structures/index.md)：汇总高阶API在Host侧Tiling接口中使用的Ascend C公共类型，包含TensorShape、TensorDataType等数据结构定义。
- [HCCL通信类](hccl_communication/index.md)：汇总Ascend C SIMD高阶API中的HCCL集合通信接口，包含Kernel侧、Tiling侧及HCCL Context管理接口。
- [索引计算](index_compute/index.md)：给定起始值，等差值和长度，返回一个等差数列。
- [数学计算](math_compute/index.md)：按元素做反余弦函数计算，输入值域需在-1到1范围内
- [归一化操作](normalization/index.md)：对每一层输入做规范化处理，在batch维度上计算均值和方差进行归一化，再通过缩放和平移参数调整分布，加速训练并提升泛化能力。
- [量化操作](quantization/index.md)：按元素做伪量化计算，将int8_t等低精度数据类型伪量化为half等高精度数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种量化策略，最多支持二维输入。
- [随机函数](random_functions/index.md)：基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。
- [归约操作](reduction_operations/index.md)：在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择。
- [排序操作](sort_operations/index.md)：对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。
- [张量变换](tensor_transform/index.md)：将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。
