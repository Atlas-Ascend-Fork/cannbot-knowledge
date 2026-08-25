# c api

- [cache ctrl](cache_ctrl/index.md)：从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
- [矩阵计算](cube_compute/index.md)：用于设置Mmad计算开启FP8模式，关闭HiF8模式，使L0A/L0B Buffer中的FP8数据在参与Mmad计算前不转化为hifloat8_t类型。
- [矩阵数据搬运](cube_data_move/index.md)：将数据从GM搬运到L0A Buffer。
- [废弃接口](deprecated_interface/index.md)：已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。
- [enum](enum/index.md)：用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。
- [通用说明和约束（C API）](general_description_and_constraints.md)：AI Core内外包含多级存储单元，各存储单元的主要用途如下：
- [misc](misc/index.md)：本接口将当前AI Core上可能由前序算子遗留的全局状态恢复为接口约定的初始状态，避免这些状态影响当前算子的计算结果
- [Reg矢量计算](reg/index.md)：寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。
- [标量计算](scalar_compute/index.md)：对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。
- [simd atomic](simd_atomic/index.md)：获取原子操作启用位与原子操作类型的值，可用于校验设置的原子配置是否符合预期。
- [struct](struct/index.md)：fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。
- [sync](sync/index.md)：用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。
- [sys var](sys_var/index.md)：该接口已废弃，请使用asc_get_squeeze_status实现此功能。 读取指定特殊寄存器的值。
- [vector compute](vector_compute/index.md)：asc_abs（矢量计算）
- [矢量数据搬运](vector_data_move/index.md)：GM到UB数据搬运接口集合，包含不同架构版本。
