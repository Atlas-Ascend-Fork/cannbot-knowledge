# Memory矢量计算

- [基础算术](vector_arith/index.md)：按元素取绝对值，计算公式如下： $$ dst_i = |src_i| $$
- [广播操作](vector_broadcast/index.md)：给定一个输入矢量，每一次取输入矢量中的8个数填充到结果矢量的8个datablock（32Bytes）中去，每个数对应一个datablock。
- [比较计算](vector_compare/index.md)：比较src0与src1在对应索引位置的元素大小。若比较结果为真，则输出结果的对应比特位设为1，否则设为0。
- [类型转换](vector_convert/index.md)：将bfloat16_t类型数据转为float，无舍入模式。
- [复合计算](vector_fused/index.md)：按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。计算公式如下：
- [聚合操作](vector_gather/index.md)：将src按照src_offset给定的偏移按元素收集到dst中。
- [逻辑计算](vector_logic/index.md)：执行矢量与运算。计算公式如下：
- [掩码操作](vector_mask_config/index.md)：设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
- [排布变换](vector_permute_sel/index.md)：执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择。
- [归约计算](vector_reduce/index.md)：执行数据块内的求最大值规约（Reduce Max）操作。
- [排序计算](vector_sort/index.md)：位图排序函数，一次迭代可以完成32个元素的排序，数据按如下描述结构进行保存：
