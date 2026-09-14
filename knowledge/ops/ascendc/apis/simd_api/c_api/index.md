# API列表

- [原子操作](atomic/index.md)：数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。
- [API列表](c_api.md)：C API文档按最细粒度公共头文件归类。除试验接口外，整体使用时可以包含c_api/asc_simd.h。
- [缓存控制](cache_ctrl/index.md)：从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
- [矩阵计算](cube_compute/index.md)：本接口用于设置Mmad计算关闭HF32模式，其作用与asc_enable_hf32相反，两个接口不同时生效。关闭HF32模式后，L0A Buffer与L0B Buffer中的float数据在参与Mmad计算之前不做舍入处理。
- [矩阵计算搬运](cube_datamove/index.md)：将数据从GM搬运到L0A Buffer。
- [基础定义](defs/index.md)：ASC_C_API_MRGSORT_ELEMENT_LEN表示MrgSort4操作支持的队列数量，值为4。该常量用于asc_mrgsort4接口的src数组长度，以及asc_get_vms4_sr接口的sorted_num数组长度。
- [废弃接口](deprecated_interface/index.md)：已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。
- [其他操作](experimental/index.md)：本接口为试验接口，在后续版本中可能会调整或改进，不保证后续兼容性。请开发者在使用过程中关注后续版本更新。
- [通用说明和约束（C API）](general_description_and_constraints.md)：AI Core内外包含多级存储单元，各存储单元的主要用途如下：
- [Reg矢量计算](reg_compute/index.md)：从Unified Buffer（UB）中按dtype对齐的起始地址读取VL长度数据，并通过函数返回值返回或写入目的矢量数据寄存器，搬运过程中数据格式和内容保持不变。连续搬入时，需要在每次调用前手动更新源地址。该接口为易用性接口，对性能有要求时可使用asc_loadunalign或asc_loadunalign_postupdate。
- [标量计算](scalar_compute/index.md)：对一个64位无符号整数执行位清除操作，将bits中第idx位清零，其余位保持不变。返回修改后的64位无符号整数。
- [特殊寄存器访问](spr/index.md)：读取CTRL寄存器（控制寄存器）特定比特位上的值。
- [同步控制](sync/index.md)：用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。
- [工具接口](utils/index.md)：本接口将当前AI Core上可能由前序算子遗留的全局状态恢复为接口约定的初始状态，避免这些状态影响当前算子的计算结果。本接口仅初始化控制状态，不会清零Global Memory、Local Memory或用户数据。
- [Memory矢量计算](vector_compute/index.md)：按元素取绝对值，计算公式如下： $$ dst_i = |src_i| $$
- [矢量数据搬运](vector_datamove/index.md)：将数据从Unified Buffer（UB）搬运到UB。支持高维切分。

- [C API](c_api_reference.md)：C API开放芯片完备编程能力，支持以数组形式分配内存，一般基于指针编程。提供与业界一致的C语言编程体验。
