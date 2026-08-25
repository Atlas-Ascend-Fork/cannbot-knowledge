# 异常检测

- [AscendcAssert](ascendc_assert.md)：CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。
- [Assert](assert.md)：CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。
- [CheckLocalMemoryIA](check_local_memory_ia_isasi.md)：检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。
- [异常检测](exception_detection.md)：异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。
- [Trap](trap.md)：Kernel侧调试接口，NPU模式下中断AI Core运行，CPU模式下等同于assert，用于异常场景调试。
