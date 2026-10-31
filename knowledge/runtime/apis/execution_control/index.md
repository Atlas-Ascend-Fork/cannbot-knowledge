# 执行控制 API

CANN Runtime 执行控制接口：回调函数启动、Host 函数订阅、算子超时设置及异步 Reduce/随机数/任务刷新操作。

- [aclrtLaunchCallback](aclrt_launch_callback.md)：在 Stream 任务队列下发 Host 回调任务，在注册线程中执行回调。异步接口。
- [aclrtSubscribeReport](aclrt_subscribe_report.md)：注册处理 Stream 上回调函数的线程。
- [aclrtProcessReport](aclrt_process_report.md)：设置超时时间，等待 aclrtLaunchCallback 下发的回调任务执行。
- [aclrtUnSubscribeReport](aclrt_un_subscribe_report.md)：取消线程注册，Stream 上的回调函数不再由指定线程处理。
- [aclrtGetOpTimeOutInterval](aclrt_get_op_time_out_interval.md)：获取硬件支持的算子超时配置的最短时间间隔。
- [aclrtSetOpExecuteTimeOut](aclrt_set_op_execute_time_out.md)：设置算子执行的超时时间（秒），进程内多次调用以最后一次为准。
- [aclrtSetOpExecuteTimeOutV2](aclrt_set_op_execute_time_out_v2.md)：设置算子执行超时时间（微秒），返回实际生效的超时时间。
- [aclrtSetOpExecuteTimeOutWithMs](aclrt_set_op_execute_time_out_with_ms.md)：设置算子执行超时时间（毫秒），当前产品均未支持。
- [aclrtGetOpExecuteTimeout](aclrt_get_op_execute_timeout.md)：查询算子实际执行超时，返回毫秒值；已设置时返回实际值，未设置时返回默认超时。
- [aclrtGetThreadLastTaskId](aclrt_get_thread_last_task_id.md)：获取当前线程最后一次下发任务的 taskId；仅记录向显式创建的 Stream 下发的任务。
- [aclrtReduceAsync](aclrt_reduce_async.md)：在指定 Stream 异步执行 SUM、MIN 或 MAX 归约；源、目标内存与 Stream 须位于同一 Device，支持的数据类型依产品而定。
- [aclrtLaunchHostFunc](aclrt_launch_host_func.md)：在 Stream 任务队列下发 Host 回调任务，内部创建并注册线程执行回调。
- [aclrtRandomNumAsync](aclrt_random_num_async.md)：下发并执行随机数生成任务。异步接口。
- [aclrtTaskUpdateAsync](aclrt_task_update_async.md)：异步刷新模型绑定流中的指定任务；taskStream 与 taskId 标识待刷新任务，execStream 指定执行刷新任务的流。
- [aclrtCacheLastTaskOpInfo](aclrt_cache_last_task_op_info.md)：捕获模式下缓存算子信息到最后下发的任务上。
- [aclrtCacheLastTaskExtendInfo](aclrt_cache_last_task_extend_info.md)：捕获模式下缓存自定义扩展信息到最后下发的任务上。
