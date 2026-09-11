# Memory矢量计算

- [基础算术](basic_arithmetic/index.md)：单目矢量计算接口，对输入tensor按元素取绝对值。
- [比较与选择](compare_and_select/index.md)：逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
- [复合计算](composite_compute/index.md)：将src0与src1相减再求绝对值，并将计算结果写入dst。
- [数据排布转换](data_layout_conversion/index.md)：将NCHW格式转换为NC1HWC0格式，也可用于二维矩阵数据块转置，单次repeat可处理512字节数据。
- [数据搬运](data_move/index.md)：支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。
- [数据搬运辅助配置接口](data_move_aux_config/index.md)：刷新NDDMA DataCache，确保多核场景下DataCopy多维搬运前缓存数据为最新状态。
- [数据填充](data_padding/index.md)：数据填充接口，每次取输入张量8个数，将每个数填充到结果张量一个DataBlock（32字节）中。
- [数据重排（ISASI）](data_rearrange_isasi/index.md)：将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。
- [逻辑计算](logical_compute/index.md)：对LocalTensor中的元素做按位与运算，支持整个tensor、前n个数据连续计算和高维切分计算三种调用方式。
- [掩码操作](mask_operations/index.md)：恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
- [归约计算](reduction_compute/index.md)：概述 Tensor 归约计算及 ReduceSum、ReduceMax、ReduceMin、ReducePairElem 等接口能力。
- [归约计算辅助配置接口](reduction_compute_aux_config/index.md)：获取ReduceRepeat或ReduceMax/ReduceMin计算的最值及索引，结果以全局变量形式存储。
- [离散与聚合](scatter_gather/index.md)：根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。
- [SIMD计算说明](simd_compute/index.md)：连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维Tensor的连续计算问题。
- [排序组合（ISASI）](sort_and_merge_isasi/index.md)：与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。
- [类型转换](type_conversion/index.md)：根据源操作数和目的操作数的数据类型进行精度转换，支持多种舍入模式。
- [类型转换辅助配置接口](type_conversion_aux_config/index.md)：设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。
- [Vector逻辑架构](vector_logical_arch/index.md)：Vector计算单元专用于执行向量计算。如下图所示，高亮部分展示了Vector计算单元及其关联的存储单元。
