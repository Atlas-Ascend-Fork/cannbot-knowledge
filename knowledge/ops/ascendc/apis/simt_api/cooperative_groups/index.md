# 协作组

- [binary_partition](binary_partition.md)：根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。
- [CoalescedGroup](coalesced_group/index.md)：判断coalesced_group组内所有线程的输入是否均不为0。
- [协作组](cooperative_groups.md)：SIMT API协作组类接口汇总，提供grid_group、thread_block、coalesced_group、thread_block_tile等线程组抽象与同步能力。
- [协作组简介](cooperative_groups_intro.md)：协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作。
- [GridGroup](grid_group/index.md)：获取当前线程所属线程块在Grid中的三维索引。
- [sync（协作组）](sync.md)：同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。
- [ThreadBlock](thread_block/index.md)：获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。
- [ThreadBlockTile](thread_block_tile/index.md)：判断thread_block_tile组内所有线程的输入是否均不为0。
- [tiled_partition](tiled_partition.md)：将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。
