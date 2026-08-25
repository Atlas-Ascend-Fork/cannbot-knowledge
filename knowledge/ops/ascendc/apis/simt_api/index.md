# simt api

- [地址空间转换函数](address_space_conversion_functions/index.md)：将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。
- [地址空间谓词函数](address_space_predicate_functions/index.md)：判断输入的指针是否指向Global Memory内存空间的地址。
- [原子操作](atomic_operations/index.md)：对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。
- [协作组](cooperative_groups/index.md)：根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。
- [数学函数](math_functions/index.md)：bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。
- [访存函数](memory_access_functions/index.md)：该接口用于刷新核内的整个Data Cache，保证数据读取时Cache的一致性。 在SIMT编程中，写入数据时会立即写入Global Memory，使其他核可见，因此不存在核间一致性问题。当从Global Memory读取数据时，该数...
- [SIMT API概述](overview.md)：SIMT API是面向AI处理器的并行计算编程接口，可以实现高效的数据并行计算。SIMT API支持两种编程模型：SIMT编程、SIMD与SIMT混合编程，用户可先阅读SIMT编程简介和SIMD与SIMT混合编程简介，以了解编程基础，后续章节将详细介绍API接口。
- [SimdSimtHybridProgrammingIntro](simd_simt_hybrid_programming_intro/index.md)：SIMD与SIMT混合编程提供了一系列适用于Device侧的数据类型，包括标量、短向量和dim3结构体。
- [SIMT编程简介](simt_programming_intro/index.md)：SIMT编程提供了一系列适用于Device侧的数据类型，包括标量、短向量以及dim3结构体。
- [同步与内存栅栏](sync_and_memory_fence/index.md)：内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。
- [Warp函数](warp_functions/index.md)：提供Lane ID获取与Lane掩码比较接口。
