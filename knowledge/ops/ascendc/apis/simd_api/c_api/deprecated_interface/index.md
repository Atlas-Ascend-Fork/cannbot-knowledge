# 废弃接口

- [AscAbsSync](asc_abs_sync_deprecated.md)：已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。
- [asc_set_atomic_add_int（废弃）](asc_set_atomic_add_int_deprecated.md)：该接口已废弃，请使用asc_set_atomic_add_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到Global Memory的数据传输开启原子累加。累加的数据类型为in...
- [废弃接口](deprecated_interface.md)：废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。
