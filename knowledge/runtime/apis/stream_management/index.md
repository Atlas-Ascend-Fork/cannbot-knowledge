# Stream 管理 API

CANN Runtime Stream 管理接口：Stream 创建、销毁、同步、查询及属性配置。

- [aclrtCreateStream](aclrt_create_stream.md)：C 单参数接口显式创建默认优先级的 Stream，作为任务下发队列；调用本接口不能指定 priority 或 flag。
- [aclrtCreateStreamWithConfig](aclrt_create_stream_with_config.md)：创建带优先级和 flag 的 Stream，支持快速下发/同步/持久化等模式。
- [aclrtDestroyStream](aclrt_destroy_stream.md)：销毁 Stream，等待任务完成后销毁。
- [aclrtDestroyStreamForce](aclrt_destroy_stream_force.md)：强制销毁 Stream，不等待任务完成。
- [aclrtSynchronizeStream](aclrt_synchronize_stream.md)：C 单参数接口阻塞 Host 当前线程，等待指定 Stream 任务完成；读取同一流的异步结果前使用，需限时等待时改用 WithTimeout。
- [aclrtSynchronizeStreamWithTimeout](aclrt_synchronize_stream_with_timeout.md)：阻塞 Host 当前线程等待 Stream 完成，支持毫秒级超时；-1 为永久等待，超时返回 Stream 同步超时错误。
- [aclrtStreamQuery](aclrt_stream_query.md)：非阻塞查询 Stream 任务是否全部完成，返回 COMPLETE 或 NOT_READY；持久化、Device 专用和 CPU 调度流的状态无业务语义。
- [aclrtStreamGetId](aclrt_stream_get_id.md)：获取指定 Stream 的 ID。
- [aclrtGetStreamAvailableNum](aclrt_get_stream_available_num.md)：获取当前 Device 上剩余可用的 Stream 数量。
- [aclrtStreamGetPriority](aclrt_stream_get_priority.md)：查询指定 Stream 的优先级。
- [aclrtStreamGetFlags](aclrt_stream_get_flags.md)：查询创建 Stream 时设置的 flag。
- [aclrtSetStreamOverflowSwitch](aclrt_set_stream_overflow_switch.md)：设置指定 Stream 后续新任务的溢出检测开关，已下发任务不变；关闭后不能通过溢出检测算子获取溢出结果。
- [aclrtGetStreamOverflowSwitch](aclrt_get_stream_overflow_switch.md)：获取指定 Stream 的溢出检测开关状态。
- [aclrtSetStreamFailureMode](aclrt_set_stream_failure_mode.md)：设置任务失败后继续执行或遇错即停，每条 Stream 仅可设置一次；遇错即停会影响同一 Context 下其他流。
- [aclrtNonBlockingLaunchBegin](aclrt_non_blocking_launch_begin.md)：开始 Stream 的异步下发区间，使同步流或 LAUNCH_BLOCKING 模式下的 Launch 保持异步；须与 End 配对，可嵌套。
- [aclrtNonBlockingLaunchEnd](aclrt_non_blocking_launch_end.md)：结束 NonBlockingLaunchBegin 区间；所有嵌套结束且 Stream 为同步模式时，等待已下发任务完成。
- [aclrtStreamAbort](aclrt_stream_abort.md)：停止指定 Stream 上正在执行的任务，丢弃已下发但未执行的任务。
- [aclrtSetStreamAttribute](aclrt_set_stream_attribute.md)：设置已创建 Stream 的溢出检测、Launch Blocking 等属性；不同于创建前设置 StreamConfigHandle 配置。
- [aclrtGetStreamAttribute](aclrt_get_stream_attribute.md)：获取 Stream 属性值。
- [aclrtActiveStream](aclrt_active_stream.md)：在已绑定模型的 Stream 上异步激活另一条已绑定 Stream，使目标流任务与当前流并行执行。
- [aclrtSwitchStream](aclrt_switch_stream.md)：比较 Device 内存中的条件值并异步跳转到目标 Stream，成功后当前流停止执行；falseStream 必须为 NULL。
- [aclrtRegStreamStateCallback](aclrt_reg_stream_state_callback.md)：按唯一名称注册 Stream 创建、销毁等状态回调，覆盖显式流和默认流；传 NULL 回调取消注册，不允许同名重复注册。
- [aclrtStreamStop](aclrt_stream_stop.md)：停止 Stream 正在执行的任务，保留尚未执行的任务；不支持默认流或已绑定模型的 Stream。
- [aclrtPersistentTaskClean](aclrt_persistent_task_clean.md)：清理 ACL_STREAM_PERSISTENT 流中的任务并保留 Stream，供后续重新下发任务，不用于普通流。
- [aclrtCreateStreamV2](aclrt_create_stream_v2.md)：按 Stream 配置句柄创建 Stream；先用 CreateStreamConfigHandle 创建配置，再用 SetStreamConfigOpt 设置属性。
- [aclrtSetStreamConfigOpt](aclrt_set_stream_config_opt.md)：向 Stream 配置句柄写入属性值及长度，供 aclrtCreateStreamV2 创建流时使用；与运行中 Stream 属性设置区分。
- [aclrtSubscribeHostFunc](aclrt_subscribe_host_func.md)：为 IPV350 的 CPU 算子调度注册用户创建的回调处理线程；每条 Stream 只能注册一个线程，一线程可服务多流。
- [aclrtProcessHostFunc](aclrt_process_host_func.md)：在用户创建并经 SubscribeHostFunc 注册的线程中等待、处理 Host 回调；timeout 以毫秒计，-1 为无限等待。
- [aclrtUnSubscribeHostFunc](aclrt_un_subscribe_host_func.md)：取消线程注册，Stream 上的回调不再由指定线程处理。
