# 调试接口

- [CPU孪生调试](cpu_twin_debug/index.md)：CPU 孪生调试接口集，包含 GmAlloc、ICPU_RUN_KF、ICPU_SET_TILING_KEY、SetKernelMode 等。
- [调试接口](debug_interface.md)：AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。
- [关闭ASCENDC_DUMP说明](disable_ascendc_dump.md)：调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。
- [异常检测](exception_detection/index.md)：CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。
- [上板打印](onboard_print/index.md)：打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。
- [性能统计](performance_stats/index.md)：推荐使用asc_mark_stamp接口进行特定位置的标记，该接口同时适用于C语言和C++语言编程。 用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。
