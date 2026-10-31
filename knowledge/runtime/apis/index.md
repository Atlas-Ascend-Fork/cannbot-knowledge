# Runtime API

CANN Runtime 主机侧 API 知识卡：接口语义、内部行为边界、错误场景与调用约束。

- [Device 管理](device_management/index.md)：Device 指定、信息查询、P2P 访问、资源限制与 Reset 相关接口（16 API）。
- [Context 管理](context_management/index.md)：Context 创建、销毁、切换与查询接口（9 API）。
- [Stream 管理](stream_management/index.md)：Stream 创建、销毁、同步、属性与异常处理接口（29 API）。
- [Event 管理](event_management/index.md)：Event 创建、记录、查询、同步与跨进程共享接口（22 API）。
- [内存管理](memory_management/index.md)：Device/Host 内存分配释放、内存拷贝、虚拟内存、统一寻址、内存池等接口（99 API）。
- [Notify 管理](notify_management/index.md)：Notify 与 CntNotify 创建、记录、等待/重置及跨进程共享接口（16 API）。
- [Label 管理](label_management/index.md)：标签创建、设置、销毁及基于索引的 Stream 跳转接口（6 API）。
- [执行控制](execution_control/index.md)：回调注册、超时设置、异步 Reduce 及主机函数启动接口（16 API）。
- [异常处理](exception_handling/index.md)：异常回调注册、错误信息查询、UCE 修复及任务中止接口（16 API）。
- [Kernel 加载与执行](kernel_loading_and_execution/index.md)：二进制加载、核函数查询、参数组装及 Kernel 启动接口（42 API）。
- [运行时配置](runtime_configuration/index.md)：aclInit/aclFinalize 家族初始化与资源限制配置接口（20 API）。
- [模型运行实例管理](model_running_instance_management/index.md)：模型运行实例的构建、执行、销毁与条件处理接口（38 API）。
- [Group 管理](group_management/index.md)：Group 设置、查询与信息获取接口（6 API）。
- [数据传输](data_transmission/index.md)：Tensor 通道、共享队列与共享缓冲区管理接口（31 API）。
- [Dump 配置](dump_configuration/index.md)：Dump 初始化、设置、回调与算子 Dump 控制接口（10 API）。
- [性能数据采集](profiling_data_collection/index.md)：Profiling 初始化、msproftx 扩展、算子信息订阅与迭代时间接口（33 API）。
- [快照管理](snapshot_management/index.md)：进程快照的加锁、备份、恢复与回调接口（6 API）。
- [错误上报](error_reporting/index.md)：内部/预定义/用户定义错误消息上报与格式化接口（4 API）。
- [日志接口](log_apis/index.md)：Alog/acllog 记录与级别检查、回调注册接口（8 API）。
- [其他辅助接口](other_apis/index.md)：版本获取、数据类型转换、能力查询、Cache 操作等辅助接口（8 API）。
- [算子 API](operation_apis/index.md)：DataBuffer、Allocator、StreamConfig、tdtDataItem/Dataset/QueueRoute 等算子辅助接口（50 API）。
- [C++ 扩展 API](cpp_extension_apis/index.md)：C++ 同步、内存分配拷贝、UVM、设备符号等扩展接口（28 API）。
- [API Hook 接口](api_hook_interfaces/index.md)：API 注入设置与获取接口（2 API）。
