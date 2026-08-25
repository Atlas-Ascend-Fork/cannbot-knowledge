# basic api

- [原子操作](atomic_operations/index.md)：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
- [辅助数据结构](aux_data_structures/index.md)：AscendC 矢量计算基础 API 的辅助数据结构总览，涵盖 Coordinate、Layout、TensorTrait、TensorDesc 等类型与参数结构。
- [缓存控制](cache_control/index.md)：AscendC 矢量计算基础 API 的缓存控制接口集，包含 DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad 等。
- [cube compute](cube_compute/index.md)：针对Ascend 950PR/Ascend 950DT产品：
- [矩阵计算（TensorAPI，试验特性）](cube_compute_tensor_api/index.md)：矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。
- [cube group mgmt](cube_group_mgmt/index.md)：Cube 分组管理（ISASI）接口总览，涵盖 CubeResGroupHandle、GroupBarrier、KfcWorkspace 等组件。
- [数据搬运导览](data_move_guide/index.md)：数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。
- [数据结构(TensorAPI，试验特性)](data_structure_tensor_api/index.md)：TensorAPI（试验特性）数据结构总览，涵盖内置数据类型、Layout 与 Tensor 相关数据结构及工具接口。
- [数据结构](data_structures/index.md)：Ascend C提供b8\~b64（8bit\~64bit）四种不同位宽的数据类型，不同位宽对应的数据类型如下表所示。
- [调试接口](debug_interface/index.md)：CPU 孪生调试接口集，包含 GmAlloc、ICPU_RUN_KF、ICPU_SET_TILING_KEY、SetKernelMode 等。
- [Kernel Tiling](kernel_tiling/index.md)：拷贝指定大小的数组内容到目标数组中，并返回指向拷贝后数组的指针。适用于拷贝一个结构体的数组成员变量的场景。该宏将指定数组拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。
- [Memory矢量计算](memory_vector_compute/index.md)：单目矢量计算接口，对输入tensor按元素取绝对值。
- [Reg矢量计算](reg_vector_compute/index.md)：Reg矢量计算辅助数据类型索引页，汇总PostLiteral、RegLayout、MaskMergeMode、SatMode与RoundMode。
- [资源管理](resource_management/index.md)：自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。
- [标量计算](scalar_compute/index.md)：将float类型标量数据转换为bfloat16_t类型标量数据。
- [特殊寄存器访问](special_register_access/index.md)：对指定的特殊寄存器进行清零操作。
- [同步控制](sync_control/index.md)：核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
- [工具接口](tool_interface/index.md)：通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。
