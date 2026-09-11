# SIMT API

- [地址空间转换函数](address_space_conversion_functions/index.md)：将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。
- [地址空间谓词函数](address_space_predicate_functions/index.md)：判断输入的指针是否指向Global Memory内存空间的地址。
- [原子操作](atomic_operations/index.md)：对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。
- [协作组](cooperative_groups/index.md)：根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。
- [数学函数](math_functions/index.md)：获取输入数据的绝对值。
- [访存函数](memory_access_functions/index.md)：该接口用于刷新核内的整个Data Cache，保证数据读取时Cache的一致性。 在SIMT编程中，写入数据时会立即写入Global Memory，使其他核可见，因此不存在核间一致性问题。当从Global Memory读取数据时，该数据可能已被其他核修改，此时应使用dcci接口直接访问Global Memory，以获取最新数据。 请注意，该接口耗时较大，性能敏感的场景慎用。
- [SIMT API概述](overview.md)：SIMT API是面向AI处理器的并行计算编程接口，可以实现高效的数据并行计算。SIMT API支持两种编程模型：SIMT编程、SIMD与SIMT混合编程，用户可先阅读SIMT编程简介和SIMD与SIMT混合编程简介，以了解编程基础，后续章节将详细介绍API接口。
- [SIMD与SIMT混合编程简介](simd_simt_hybrid_programming_intro/index.md)：SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。
- [SIMT编程简介](simt_programming_intro/index.md)：SIMT编程模型采用Grid、Thread Block、Warp、Thread分层线程结构，适合控制流复杂和访存模式不规则的算子场景。
- [同步与内存栅栏](sync_and_memory_fence/index.md)：SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。
- [Warp函数](warp_functions/index.md)：Warp是SIMT线程执行和调度的基本单位。一个线程块内的线程会按照线性线程号被划分为多个Warp，当前一个Warp包含32个线程。同一Warp内的线程执行相同的指令流，但每个线程拥有独立的寄存器和Lane ID，可处理不同的数据地址和分支路径。
