# 基础API

- [原子操作](atomic_operations/index.md)：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
- [辅助数据结构](aux_data_structures/index.md)：BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
- [缓存控制](cache_control/index.md)：解决Data Cache与GM一致性问题，将脏数据写回GM并将指定Cache Line标记为无效，确保下次访问从GM重新加载。
- [矩阵计算（ISASI）](cube_compute_isasi/index.md)：针对Ascend 950PR/Ascend 950DT产品：
- [Cube分组管理（ISASI）](cube_group_mgmt_isasi/index.md)：AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图 !
- [数据搬运导览](data_move_guide/index.md)：提供Global Memory与L1 Buffer及L0 Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及矩阵计算结果搬出等场景。
- [数据结构](data_structures/index.md)：Ascend C提供b8\~b64（8bit\~64bit）四种不同位宽的数据类型，不同位宽对应的数据类型如下表所示。
- [调试接口](debug_interface/index.md)：调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。
- [Kernel Tiling](kernel_tiling/index.md)：拷贝指定大小的数组内容到目标数组中，并返回指向拷贝后数组的指针。适用于拷贝一个结构体的数组成员变量的场景。该宏将指定数组拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。
- [Memory矢量计算](memory_vector_compute/index.md)：单目矢量计算接口，对输入tensor按元素取绝对值。
- [Reg矢量计算](reg_vector_compute/index.md)：Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。
- [资源管理](resource_management/index.md)：获取创建TPipe对象时设置的全局唯一TPipe指针，获取后可进行TPipe相关的操作如InitBuffer。
- [标量计算](scalar_compute/index.md)：将float类型标量数据转换为bfloat16_t类型标量数据。
- [特殊寄存器访问](special_register_access/index.md)：对指定的特殊寄存器进行清零操作。
- [同步控制](sync_control/index.md)：在编程中，同步是指协调多个执行单元（如线程、进程等）对共享资源的访问顺序和时机来确保程序的正确性。如果没有同步来严格控制执行顺序，则会出现结果不一致、行为不可预测等多种问题。
- [工具接口](tool_interface/index.md)：通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。
