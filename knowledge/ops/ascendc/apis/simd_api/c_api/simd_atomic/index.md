# simd atomic

- [AscGetStoreAtomicConfig](asc_get_store_atomic_config.md)：获取原子操作启用位与原子操作类型的值，可用于校验设置的原子配置是否符合预期。
- [AscSetAtomicAdd](asc_set_atomic_add.md)：对后续目的地址为GM的数据搬运指令开启原子累加，将待搬运数据与GM已有数据求和后写入GM。
- [AscSetAtomicMax](asc_set_atomic_max.md)：对后续从UB/L0C/L1到GM的数据传输开启原子比较取大，将待拷贝内容与GM已有内容比较后取最大值写入GM。
- [asc_set_atomic_max_int（废弃）](asc_set_atomic_max_int_deprecated.md)：该接口已废弃，请使用asc_set_atomic_max_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最大值写入GM。
- [AscSetAtomicMin](asc_set_atomic_min.md)：对后续从UB/L0C/L1到GM的数据传输开启原子比较取小，将待拷贝内容与GM已有内容比较后取最小值写入GM。
- [asc_set_atomic_min_int（废弃）](asc_set_atomic_min_int_deprecated.md)：该接口已废弃，请使用asc_set_atomic_min_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最小值写入GM。
- [AscSetAtomicNone](asc_set_atomic_none.md)：清空原子操作状态，与原子加、取大、取小接口配合使用，在完成原子操作后关闭原子操作。
- [AscSetStoreAtomicConfigV1](asc_set_store_atomic_config_v1.md)：设置原子操作启用位与原子操作类型的值。
- [asc_set_store_atomic_config_v2（废弃）](asc_set_store_atomic_config_v2_deprecated.md)：该接口已废弃。原子加操作请使用asc_atomic_add实现。 设置原子操作启用位与原子操作类型的值。
- [原子操作](atomic_operations.md)：SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。
- [原子操作概述（SIMD原子操作）](atomic_operations_overview.md)：数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启...
- [关键特性说明（SIMD原子操作）](key_features.md)：确定性计算是指在相同输入条件下，无论执行次数或执行环境如何变化，总能产生完全一致输出结果的计算过程。确定性计算为系统稳定性和实验可验证性提供保障。
