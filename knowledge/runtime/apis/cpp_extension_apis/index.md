# Runtime C++ 扩展 API

CANN Runtime C++ 扩展接口（C++ 重载/模板封装）：为 C++ 场景提供类型安全的简化 API，内部调用对应 C 接口实现。适用于 C++ 程序。

## 同步与调度简化接口

- [aclrtSynchronizeDevice](aclrt_synchronize_device.md)：C++ 带 timeout 的 Device 同步封装，阻塞当前 Host 线程等待当前 Context 对应 Device；-1 永久等待，正值以毫秒计。
- [aclrtSynchronizeStream](aclrt_synchronize_stream.md)：C++ 带 timeout 的 Stream 同步封装，调用 aclrtSynchronizeStreamWithTimeout；-1 永久等待，正值为毫秒超时。
- [aclrtSynchronizeEvent](aclrt_synchronize_event.md)：C++ 带 timeout 的 Event 同步封装，阻塞当前 Host 线程等待捕获任务完成；-1 永久等待，正值以毫秒计。
- [aclrtStreamWaitEvent](aclrt_stream_wait_event.md)：C++ 三参数 Event 等待封装，调用 aclrtStreamWaitEventWithTimeout；异步阻塞指定 Stream，timeout 为 0 表示不超时。
- [aclrtCreateStream](aclrt_create_stream.md)：C++ Stream 创建封装，接收 priority 和 flag，转调 aclrtCreateStreamWithConfig；用于选择优先级和流模式。
- [aclrtSetOpExecuteTimeOut](aclrt_set_op_execute_time_out.md)：C++ 双参数算子超时封装，调用 aclrtSetOpExecuteTimeOutV2；以微秒设置并返回实际生效值，任务自身超时优先。
- [aclrtCreateEvent](aclrt_create_event.md)：C++ 双参数 Event 创建封装，调用 aclrtCreateEventExWithFlag；由 flag 选择计时、同步或 IPC，资源不受硬件数量限制。

## 内存分配与拷贝模板接口

- [aclrtMalloc](aclrt_malloc.md)：C++ 模板申请 Device 内存，返回类型化指针，可指定 policy 和 cfg；内部调用 aclrtMallocWithCfg，首地址 64 字节对齐。
- [aclrtMallocHost](aclrt_malloc_host.md)：C++ 模板申请 64 字节对齐的 Host 锁页内存，可传 cfg；内部调用 aclrtMallocHostWithCfg，配对 FreeHost 释放。
- [aclrtMemcpy](aclrt_memcpy.md)：C++ 类型化指针的同步复制封装，转调同名 C 接口；复制方向由源、目的地址判断，kind 为预留参数。
- [aclrtMemcpyAsync](aclrt_memcpy_async.md)：C++ 类型化指针的 Stream 复制封装；Host 锁页内存下异步、需同步等待，非锁页内存下完成后返回。
- [aclrtMemcpy2d](aclrt_memcpy2d.md)：C++ 模板同步复制二维矩阵区域，分别指定源、目的 pitch 及 width、height，内部调用同名 C 接口。
- [aclrtMemcpy2dAsync](aclrt_memcpy2d_async.md)：C++ 模板向 Stream 下发带源、目的 pitch 的二维复制；Host 锁页内存下异步，非锁页内存下完成后返回。
- [aclrtMemcpyBatch](aclrt_memcpy_batch.md)：C++ 批量同步复制模板，调用 aclrtMemcpyBatchV2；支持统一或分组属性，无失败下标输出参数。
- [aclrtMemcpyBatchAsync](aclrt_memcpy_batch_async.md)：C++ 批量 Stream 复制模板，调用 aclrtMemcpyBatchAsyncV2；无失败下标输出，Host 非锁页内存下完成后返回。

## 指针与 Host 内存管理模板接口

- [aclrtPointerGetAttributes](aclrt_pointer_get_attributes.md)：C++ 模板查询指针的 Host/Device 位置、页表大小等属性；不能传 Host 注册映射得到的 Device 地址。
- [aclrtHostRegister](aclrt_host_register.md)：C++ Host 内存注册模板：type 重载直接返回 Device 指针，flag 重载支持映射或将非锁页内存注册为锁页内存。
- [aclrtHostGetDevicePointer](aclrt_host_get_device_pointer.md)：C++ 模板根据已注册的 Host 指针获取同类型的 Device 映射指针；预留 flag 必须为 0。
- [aclrtHostUnregister](aclrt_host_unregister.md)：C++ 模板以原始 Host 指针取消内存注册，与 aclrtHostRegister 配对，内部调用同名 C 接口。

## 统一虚拟内存（UVM）模板接口

- [aclrtMemAllocManaged](aclrt_mem_alloc_managed.md)：C++ 模板申请 Host/Device 统一编址的 UVM 内存，大小向上按 2MB 对齐；返回类型化指针，使用 aclrtFree 释放。
- [aclrtMemManagedPrefetchAsync](aclrt_mem_managed_prefetch_async.md)：C++ 模板向指定 Stream 下发单段 UVM 预取，长度须 2MB 对齐；成功仅表示下发，完成需同步等待。
- [aclrtMemManagedPrefetchBatchAsync](aclrt_mem_managed_prefetch_batch_async.md)：C++ 模板批量预取 UVM，支持全部内存共用一个位置或按索引分组指定位置；完成需同步 Stream。

## Device 变量操作模板接口

- [aclrtGetSymbolAddress](aclrt_get_symbol_address.md)：C++ 模板按 __gm__ 变量名获取 Device 地址，用于 Ascend C 混合编译；地址仅在当前 Device 有效。
- [aclrtGetSymbolSize](aclrt_get_symbol_size.md)：C++ 模板按 __gm__ 变量名查询 Device 变量占用的字节数，用于 Ascend C 混合编译场景。
- [aclrtMemcpyFromSymbol](aclrt_memcpy_from_symbol.md)：C++ 模板按 __gm__ 变量名及偏移，将 Device 变量同步读到 Host；offset 与 count 之和须在变量范围内。
- [aclrtMemcpyFromSymbolAsync](aclrt_memcpy_from_symbol_async.md)：C++ 模板按 __gm__ 变量名将 Device 数据读到 Host，指定偏移和 Stream；Host 锁页内存下异步，非锁页下同步返回。
- [aclrtMemcpyToSymbol](aclrt_memcpy_to_symbol.md)：C++ 模板按 __gm__ 变量名及偏移，将 Host 数据同步写入 Device 变量；offset 与 count 之和须在变量范围内。
- [aclrtMemcpyToSymbolAsync](aclrt_memcpy_to_symbol_async.md)：C++ 模板按 __gm__ 变量名将 Host 数据写入 Device，指定偏移和 Stream；Host 锁页内存下异步，非锁页下同步返回。
