# 归约计算

- [AscPairReduceSum](asc_pair_reduce_sum.md)：将源操作数中每两个相邻数值相加，结果连续保存在目的操作数的低半部分。
- [AscReduceMax](asc_reduce_max.md)：根据mask对源操作数进行归约最大值操作，将最大值及其索引写入目的操作数。
- [AscReduceMaxDatablock](asc_reduce_max_datablock.md)：根据mask将每个DataBlock中的最大值依次保存在目的操作数的最低位。
- [AscReduceMin](asc_reduce_min.md)：根据mask对源操作数进行归约最小值操作，将最小值及其索引写入目的操作数。
- [AscReduceMinDatablock](asc_reduce_min_datablock.md)：根据mask将每个DataBlock中的最小值依次保存在目的操作数的最低位。
- [AscReduceSum](asc_reduce_sum.md)：根据mask对源操作数进行归约求和操作，将所有参与计算的元素之和保存到目的操作数。
- [AscReduceSumDatablock](asc_reduce_sum_datablock.md)：根据mask将每个DataBlock中参与计算的元素相加，结果依次保存在目的操作数最低位。
- [归约计算](reduce_compute.md)：寄存器侧归约计算类接口汇总，提供sum、max、min等逐元素及DataBlock级归约能力。
