# 运行时诊断

- [AI CPU 侧调试接口边界（assert / printf / DataStoreBarrier）](aicpu_debug_interface_boundaries.md)：区分 AI CPU 的 assert、printf、DataStoreBarrier 与 AI Core 同名接口；核对异构调用域、每核单次 Dump 预算和写可见性，并用来源中的读侧同步示例排查问题。
