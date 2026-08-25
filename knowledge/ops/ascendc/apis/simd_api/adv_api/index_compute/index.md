# 索引计算

- [Arange（索引计算）](arange.md)：给定起始值，等差值和长度，返回一个等差数列。
- [GetArangeMaxMinTmpSize](get_arange_max_min_tmp_size.md)：用于获取Arange Tiling参数：Arange接口能完成计算所需最大临时空间大小max和最小临时空间大小min。 由于Arange接口内部不需要用到临时空间，max和min均返回0。
- [索引计算](index_compute.md)：提供Ascend C SIMD高阶API中的索引计算接口，包含Arange及GetArangeMaxMinTmpSize等Tiling临时空间大小查询接口。
