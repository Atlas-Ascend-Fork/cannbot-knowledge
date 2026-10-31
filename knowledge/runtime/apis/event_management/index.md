# Event 管理 API

CANN Runtime Event 管理接口：事件创建、记录、同步、计时及 IPC 跨进程共享。

- [aclrtCreateEvent](aclrt_create_event.md)：创建用于计时或跨 Stream 同步的 Event；首次 Record 才申请硬件资源，可能阻塞，不支持 aclrtResetEvent。
- [aclrtCreateEventWithFlag](aclrt_create_event_with_flag.md)：按 flag 创建计时、同步或进度捕获 Event；后续使用 ResetEvent 或 StreamWaitEvent 时须包含 ACL_EVENT_SYNC。
- [aclrtCreateEventExWithFlag](aclrt_create_event_ex_with_flag.md)：创建资源不受硬件数量限制的 Event，可用于计时、同步或 IPC；不支持 ResetEvent 和 QueryEventWaitStatus。
- [aclrtDestroyEvent](aclrt_destroy_event.md)：销毁 Event，无需阻塞等待其任务完成，资源完成后延迟释放；调用时须确保其他接口不再使用该 Event。
- [aclrtRecordEvent](aclrt_record_event.md)：在 Stream 上异步记录已下发任务的完成点，配合另一 Stream 的 WaitEvent 建立依赖，或供 Host 同步等待。
- [aclrtRecordEventWithFlag](aclrt_record_event_with_flag.md)：记录 Stream 的 Event 完成点并指定 flag；EXTERNAL 用于图捕获场景，DEFAULT 沿用普通 Record 行为。
- [aclrtResetEvent](aclrt_reset_event.md)：在 Stream 上异步复位 Event 以便复用；仅支持 WithFlag 创建且带 ACL_EVENT_SYNC 的 Event。
- [aclrtQueryEvent（废弃）](aclrt_query_event.md)：旧版 Event 完成状态查询，查询同一线程 Record 的 Event；后续版本将废弃，推荐改用 aclrtQueryEventStatus。
- [aclrtQueryEventStatus](aclrt_query_event_status.md)：非阻塞查询 Event 已捕获任务是否完成，返回 COMPLETE 或 NOT_READY；用于轮询记录点的执行状态。
- [aclrtQueryEventWaitStatus](aclrt_query_event_wait_status.md)：查询 StreamWaitEvent 下发的等待任务是否全部完成；区别于记录点状态查询，不支持 ExWithFlag 创建的 Event。
- [aclrtSynchronizeEvent](aclrt_synchronize_event.md)：阻塞 Host 当前线程，等待 Event 记录点捕获的任务完成；仅需轮询时可用 QueryEventStatus。
- [aclrtSynchronizeEventWithTimeout](aclrt_synchronize_event_with_timeout.md)：阻塞 Host 当前线程等待 Event 完成，并指定毫秒级超时；-1 表示永久等待，超时返回 Event 同步超时错误。
- [aclrtEventElapsedTime](aclrt_event_elapsed_time.md)：计算同一 Stream 中两个 Event 记录点之间的耗时，单位毫秒；须先同步 Stream，确保两者已完成。
- [aclrtEventGetTimestamp](aclrt_event_get_timestamp.md)：获取 Event 完成时相对 AI 处理器系统启动的时间戳，单位微秒；须先 Record 并同步 Stream。
- [aclrtGetEventId](aclrt_get_event_id.md)：获取指定 Event 的 ID。
- [aclrtGetEventAvailNum](aclrt_get_event_avail_num.md)：查询当前 Device 上可用的 Event 数量。
- [aclrtSetOpWaitTimeout](aclrt_set_op_wait_timeout.md)：设置进程级后续 StreamWaitEvent 任务的等待超时，单位秒，0 表示不超时；超时由同步等待接口报告。
- [aclrtStreamWaitEvent](aclrt_stream_wait_event.md)：向 Stream 异步下发 Event 等待任务，建立跨流依赖；可由多个 Stream 等待同一 Event，超时另由进程级接口配置。
- [aclrtStreamWaitEventWithFlag](aclrt_stream_wait_event_with_flag.md)：为 Stream 的 Event 等待指定超时和 flag；图捕获使用 WAIT_EXTERNAL 时，timeout 必须为 0。
- [aclrtStreamWaitEventWithTimeout](aclrt_stream_wait_event_with_timeout.md)：为指定 Stream 下发带超时的 Event 等待；timeout 须非负，0 表示不超时，可由多流等待同一 Event。
- [aclrtIpcGetEventHandle](aclrt_ipc_get_event_handle.md)：将带 ACL_EVENT_IPC 标志的 Ex Event 导出为跨进程共享句柄，用于同 Device 多进程或跨 Device 的任务同步。
- [aclrtIpcOpenEventHandle](aclrt_ipc_open_event_handle.md)：导入 aclrtIpcGetEventHandle 导出的共享句柄，取得当前进程可使用的 Event 指针，用于跨进程同步。
