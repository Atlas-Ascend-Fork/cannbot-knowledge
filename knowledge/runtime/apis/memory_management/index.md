# 内存管理 API

CANN Runtime 内存管理 API（aclrt 前缀）知识卡：设备内存分配与释放、主机内存管理、内存复制与设置、虚拟内存管理、统一寻址、CMO 缓存操作、IPC 进程间内存共享、自定义分配器、流内存操作、Stream 有序内存分配及 Device 变量内存操作。

## 设备内存分配与释放

- [aclrtMalloc](aclrt_malloc.md)：在 Device 上分配线性内存，首地址 64 字节对齐
- [aclrtMallocAlign32](aclrt_malloc_align32.md)：在 Device 上分配线性内存，仅 32 字节对齐
- [aclrtMallocCached](aclrt_malloc_cached.md)：在 Device 上分配 Cache 缓存内存
- [aclrtMallocWithCfg](aclrt_malloc_with_cfg.md)：按 policy 和 cfg 申请 Device 线性内存，支持带宽类型、用户态只读与基础分配规则组合。
- [aclrtMallocForTaskScheduler](aclrt_malloc_for_task_scheduler.md)：申请 Task 调度器可访问的 Device 内存，供图模式下需要此内存类型的算子使用，可指定分配策略和 cfg。
- [aclrtFree](aclrt_free.md)：释放 Runtime 分配的 Device 内存，不隐式同步 Device 或 Stream，也不等待使用该内存的任务完成。
- [aclrtFreeWithDevSync](aclrt_free_with_dev_sync.md)：释放 Device 内存，含隐式 Device 同步
- [aclrtMemFlush](aclrt_mem_flush.md)：将指定 DDR 地址范围的 Cache 数据写回 DDR 并置为无效；正文所述版本无需用户处理 CPU/NPU Cache 一致性。
- [aclrtMemInvalidate](aclrt_mem_invalidate.md)：将指定 DDR 地址范围的 Cache 数据置为无效；正文所述版本无需用户处理 CPU/NPU Cache 一致性。
- [aclrtGetMemInfo](aclrt_get_mem_info.md)：查询 Device 内存的空闲和总大小
- [aclrtGetMemUsageInfo](aclrt_get_mem_usage_info.md)：查询组件内存使用信息
- [aclrtCheckMemType](aclrt_check_mem_type.md)：批量检查 Device 地址是否匹配指定分配类型，支持 DEV、DVPP、RSVD 类型组合，输出 1 或 0 的匹配结果。

## 主机内存管理

- [aclrtMallocHost](aclrt_malloc_host.md)：申请 Host 锁页内存
- [aclrtMallocHostWithCfg](aclrt_malloc_host_with_cfg.md)：申请 Host 锁页内存，支持配置
- [aclrtFreeHost](aclrt_free_host.md)：释放 MallocHost 或 MallocHostWithCfg 分配的 Host 内存，不隐式同步或等待任务；需隐式 Device 同步时用 WithDevSync 变体。
- [aclrtFreeHostWithDevSync](aclrt_free_host_with_dev_sync.md)：释放 Host 内存，含隐式 Device 同步
- [aclrtHostRegister](aclrt_host_register.md)：按 type 将 Host 内存注册为 Device 可访问并直接返回映射指针；所得 Device 地址不能用于 Host 内存复制操作。
- [aclrtHostRegisterV2](aclrt_host_register_v2.md)：按 flag 注册 Host 内存，可映射或将非锁页内存注册为锁页内存；PINNED 仅适用于非锁页内存，接口不直接返回 Device 指针。
- [aclrtHostGetDevicePointer](aclrt_host_get_device_pointer.md)：从已注册的 Host 指针查询 Device 映射地址；所得地址供 Device 访问，不能用于内存复制等内存操作。
- [aclrtHostMemMapCapabilities](aclrt_host_mem_map_capabilities.md)：查询 HAC 是否支持访问注册内存
- [aclrtHostUnregister](aclrt_host_unregister.md)：使用原始 Host 地址取消内存注册，与 aclrtHostRegister 或 aclrtHostRegisterV2 成对使用。
- [aclrtHostGetDevicePointerAddrRange](aclrt_host_get_device_pointer_addr_range.md)：查询 Host 注册映射的 Device 地址范围数组；addrRange 为空时先获取数组长度，再由调用方分配空间查询。

## 内存复制与设置

- [aclrtMemcpy](aclrt_memcpy.md)：主机与设备间的同步内存复制，内部按地址自动判定复制方向；跨 Device 复制需先启用 P2P。
- [aclrtMemcpyAsync](aclrt_memcpy_async.md)：下发到指定 Stream 的内存复制；锁页内存下为异步、需 Stream 同步等待完成，非锁页内存下同步返回。
- [aclrtMemcpyAsyncWithCondition](aclrt_memcpy_async_with_condition.md)：废弃，同 aclrtMemcpyAsync
- [aclrtMemcpyBatch](aclrt_memcpy_batch.md)：批量同步内存复制；批次内无序，仅支持 Host 与 Device 间单一方向，出错经 failIndex 返回失败项下标。
- [aclrtMemcpyBatchAsync](aclrt_memcpy_batch_async.md)：下发到 Stream 的批量内存复制；批次内无序、仅支持单方向，锁页内存下异步、非锁页下同步返回。
- [aclrtMemcpyBatchV2](aclrt_memcpy_batch_v2.md)：批量同步复制（无失败下标）
- [aclrtMemcpyBatchAsyncV2](aclrt_memcpy_batch_async_v2.md)：批量异步复制（无失败下标）
- [aclrtMemcpy2d](aclrt_memcpy2d.md)：按源、目的 pitch 同步复制 width×height 的二维矩阵区域；当前仅支持 Host 与 Device 间双向复制。
- [aclrtMemcpy2dAsync](aclrt_memcpy2d_async.md)：在指定 Stream 上按源、目的 pitch 复制二维矩阵区域；支持 Host/Device 互拷，Device 间复制受产品型号限制。
- [aclrtGetMemcpyDescSize](aclrt_get_memcpy_desc_size.md)：查询当前 Device 内存复制描述符所需字节数，当前仅支持同 Device 内的 INNER_DEVICE_TO_DEVICE 复制。
- [aclrtSetMemcpyDesc](aclrt_set_memcpy_desc.md)：在 Device 描述符中记录同 Device 复制的源、目的地址和长度；先用 GetMemcpyDescSize 查询大小并申请描述符内存。
- [aclrtMemcpyAsyncWithDesc](aclrt_memcpy_async_with_desc.md)：使用预先设置的复制描述符在 Stream 上异步复制，仅支持同 Device 内复制；先查询描述符大小，再调用 SetMemcpyDesc。
- [aclrtMemcpyAsyncWithOffset](aclrt_memcpy_async_with_offset.md)：在 Stream 上执行同 Device 内的异步复制，源、目的基址以二级指针传入，并分别指定数据偏移。
- [aclrtMemset](aclrt_memset.md)：按字节同步填充 Host/Device 内存为指定值；同步执行，不隐式做流或 Device 同步。
- [aclrtMemsetAsync](aclrt_memset_async.md)：下发到 Stream 的内存填充；锁页内存下为异步、非锁页 Host 内存下同步返回。
- [aclrtMemsetD32](aclrt_memset_d32.md)：以 uint32_t 为单位同步填充内存，N 表示元素数，容量须至少 N×4 字节；不隐式同步 Device。
- [aclrtMemsetD32Async](aclrt_memset_d32_async.md)：以 uint32_t 为单位填充 N 个值，容量须至少 N×4 字节；Device 内存任务下发到 Stream，Host 内存同步执行。

## 虚拟内存管理

- [aclrtMallocPhysical](aclrt_malloc_physical.md)：申请物理内存
- [aclrtFreePhysical](aclrt_free_physical.md)：按 MallocPhysical 返回的 handle 释放物理内存；仍与虚拟地址映射时，须先调用 aclrtUnmapMem。
- [aclrtReserveMemAddress](aclrt_reserve_mem_address.md)：预留虚拟内存
- [aclrtReserveMemAddressNoUCMemory](aclrt_reserve_mem_address_no_u_c_memory.md)：由用户指定起始地址预留不支持 UC 的虚拟内存，不能自动分配地址；大小须为 1GB 的整数倍，最少 1GB。
- [aclrtReleaseMemAddress](aclrt_release_mem_address.md)：释放 ReserveMemAddress 预留的虚拟地址空间；仍映射物理内存时，须先调用 UnmapMem 解除映射。
- [aclrtMapMem](aclrt_map_mem.md)：将虚拟地址绑定到物理内存 handle；映射大小须与物理分配一致，当前 offset 和 flags 均须为 0。
- [aclrtMemMapNoAccess](aclrt_mem_map_no_access.md)：将虚拟地址绑定到物理内存但不建立可访问页表；随后须调用 MemSetAccess 设置访问权限。
- [aclrtUnmapMem](aclrt_unmap_mem.md)：取消映射
- [aclrtMemExportToShareableHandle](aclrt_mem_export_to_shareable_handle.md)：将物理内存 handle 导出为 AI Server 内跨进程共享的整数句柄，可启用 PID 白名单；跨 Device 需先开启 PeerAccess。
- [aclrtMemSetPidToShareableHandle](aclrt_mem_set_pid_to_shareable_handle.md)：为 MemExportToShareableHandle 导出的整数共享句柄设置 PID 白名单，控制物理内存的跨进程共享。
- [aclrtMemImportFromShareableHandle](aclrt_mem_import_from_shareable_handle.md)：将整数共享句柄导入到指定 Device，返回当前进程的物理内存 handle；共享内存须仍存在，不支持同进程导出再导入。
- [aclrtMemExportToShareableHandleV2](aclrt_mem_export_to_shareable_handle_v2.md)：按 shareType 导出物理内存共享句柄，可选择 AI Server 内或跨 Server 共享；跨 Server 仅 A3 支持。
- [aclrtMemSetPidToShareableHandleV2](aclrt_mem_set_pid_to_shareable_handle_v2.md)：为 V2 导出的物理内存共享句柄设置 PID 白名单，并显式指定 shareType，与 IPC 字符串 key 的白名单接口区分。
- [aclrtMemImportFromShareableHandleV2](aclrt_mem_import_from_shareable_handle_v2.md)：按 shareType 导入 V2 共享句柄，返回当前进程物理内存 handle；flags 固定为 0，不支持同进程进行 V2 导出和导入。
- [aclrtMemGetAllocationGranularity](aclrt_mem_get_allocation_granularity.md)：根据物理内存属性查询最小或推荐分配粒度，结果以字节表示，供物理内存申请时选择对齐大小。
- [aclrtMemSetAccess](aclrt_mem_set_access.md)：按访问配置数组设置虚拟内存范围的权限，起始地址必须与 MapMem 的映射地址一致。
- [aclrtMemGetAccess](aclrt_mem_get_access.md)：查询指定虚拟地址在给定内存位置 location 上的访问保护标志，返回权限而非物理内存属性。
- [aclrtMemRetainAllocationHandle](aclrt_mem_retain_allocation_handle.md)：从已映射的虚拟地址获取并保留物理内存 handle；每次调用均须配对一次 aclrtFreePhysical。
- [aclrtMemGetAllocationPropertiesFromHandle](aclrt_mem_get_allocation_properties_from_handle.md)：查询物理内存 handle 属性
- [aclrtMemGetAddressRange](aclrt_mem_get_address_range.md)：查询地址所属内存块
- [aclrtMemMapSelectedLink](aclrt_mem_map_selected_link.md)：选择链路映射虚拟地址
- [aclrtMemMapSetLink](aclrt_mem_map_set_link.md)：为已导入的物理内存 handle 设置映射访问链路；调用顺序为 ImportFromShareableHandle、SetLink、MapMem。

## 统一寻址

- [aclrtMemAllocManaged](aclrt_mem_alloc_managed.md)：申请按 2MB 向上对齐的 UVM 内存，通过缺页机制迁移，访问时建立页表；单进程上限 3TB。
- [aclrtMemManagedAdvise](aclrt_mem_managed_advise.md)：对 MemAllocManaged 分配的 UVM 范围设置或取消策略属性，并指定物理位置；操作长度须按 2MB 对齐。
- [aclrtMemManagedGetAttr](aclrt_mem_managed_get_attr.md)：查询一段 UVM 内存的单个策略属性；范围内属性值不一致时返回无效值，结果缓冲区由调用方提供。
- [aclrtMemManagedGetAttrs](aclrt_mem_managed_get_attrs.md)：对同一 UVM 地址范围批量查询多个策略属性，按属性数组分别提供结果缓冲区及其大小。
- [aclrtMemManagedPrefetchAsync](aclrt_mem_managed_prefetch_async.md)：在指定 Stream 上预取单段 UVM 到目标物理位置，长度须 2MB 对齐；调用后需同步等待预取完成。
- [aclrtMemManagedPrefetchBatchAsync](aclrt_mem_managed_prefetch_batch_async.md)：在指定 Stream 上批量预取 UVM，用索引数组将各内存段分组映射到目标物理位置；地址与长度数组须等长。
- [aclrtMemP2PMap](aclrt_mem_p2_p_map.md)：为同进程两个 Device 的内存建立跨设备页表映射；须先用 DeviceEnablePeerAccess 开启 P2P 数据交互。
- [aclrtPointerGetAttributes](aclrt_pointer_get_attributes.md)：查询指针所在位置、页表大小等内存属性；禁止传入 HostRegister 映射得到的 Device 地址。

## CMO 缓存操作

- [aclrtCmoAsync](aclrt_cmo_async.md)：向 Stream 异步下发本 Device 内存的 Cache 操作，当前仅支持 PREFETCH 预取。
- [aclrtCmoAsyncWithBarrier](aclrt_cmo_async_with_barrier.md)：向已绑定模型的 Stream 异步下发 Cache 操作；INVALID 类型可携带 barrierId，供后续屏障等待。
- [aclrtCmoWaitBarrier](aclrt_cmo_wait_barrier.md)：在已绑定模型的 Stream 上等待指定 barrierId 的 INVALID Cache 操作完成，与带屏障的 CMO 下发配合。
- [aclrtCmoGetDescSize](aclrt_cmo_get_desc_size.md)：获取 Cache 描述符大小
- [aclrtCmoSetDesc](aclrt_cmo_set_desc.md)：在已申请的 Device 描述符内存中记录 Cache 操作地址和长度；先用 CmoGetDescSize 查询描述符大小。
- [aclrtCmoAsyncWithDesc](aclrt_cmo_async_with_desc.md)：通过 CmoSetDesc 准备的 Device 描述符向 Stream 异步下发 Cache 预取，当前仅支持 PREFETCH，reserve 须为 NULL。

## IPC 进程间内存共享

- [aclrtIpcMemGetExportKey](aclrt_ipc_mem_get_export_key.md)：将 Device 地址对应的内存导出为 IPC key，支持开关进程白名单校验；key 缓冲区长度固定为 65。
- [aclrtIpcMemSetImportPid](aclrt_ipc_mem_set_import_pid.md)：为已导出的 IPC 内存 key 设置可导入进程的 PID 数组，配合 IpcMemGetExportKey 的白名单校验使用。
- [aclrtIpcMemImportPidInterServer](aclrt_ipc_mem_import_pid_inter_server.md)：批量设置 IPC 白名单（超节点）
- [aclrtIpcMemImportByKey](aclrt_ipc_mem_import_by_key.md)：按 IPC key 导入共享内存，返回当前进程的 Device 地址；可选择开启 P2P，导入前须保证共享内存未释放。
- [aclrtIpcMemSetAttr](aclrt_ipc_mem_set_attr.md)：按 IPC key 设置共享内存的访问链路属性；950 使用 UB，A3 使用 SIO/HCCS，须按产品选择属性值。
- [aclrtIpcMemClose](aclrt_ipc_mem_close.md)：按 key 关闭 IPC 共享内存；所有导入进程先完成 Close 后，导出进程才能关闭。

## 自定义内存分配器

- [aclrtAllocatorRegister](aclrt_allocator_register.md)：将自定义 Allocator 及回调绑定到 Stream，仅用于单算子模型执行和动态 shape 推理；不同流共用同一 Allocator 时不能并发。
- [aclrtAllocatorGetByStream](aclrt_allocator_get_by_stream.md)：按注册时的 Stream 查询自定义 Allocator，返回描述符、对象及分配、释放、建议地址分配和取地址回调。
- [aclrtAllocatorUnregister](aclrt_allocator_unregister.md)：按 Stream 取消自定义 Allocator 注册，须在销毁 Allocator 前调用；重复取消或 Stream 不存在时不报错。

## 流内存操作

- [aclrtValueWrite](aclrt_value_write.md)：向 Stream 异步下发 Device 内存值写入，写入 uint64_t 数据；目标地址须 8 字节对齐，flag 固定为 0。
- [aclrtValueWait](aclrt_value_wait.md)：向 Stream 异步下发内存值等待，按 GEQ、EQ、AND 或 NOR 条件比较 Device 地址中的值，满足条件后解除流阻塞。

## Stream 有序内存分配（SOMA）

- [aclrtMemPoolCreate](aclrt_mem_pool_create.md)：按配置创建内存池，供后续池内申请与复用；仅 Atlas A2 系列支持，属于不用于生产环境的试验特性。
- [aclrtMemPoolDestroy](aclrt_mem_pool_destroy.md)：销毁内存池（试验特性）
- [aclrtMemPoolSetAttr](aclrt_mem_pool_set_attr.md)：设置内存池属性（试验特性）
- [aclrtMemPoolGetAttr](aclrt_mem_pool_get_attr.md)：获取内存池属性（试验特性）
- [aclrtMemPoolMallocAsync](aclrt_mem_pool_malloc_async.md)：在指定 Stream 上从已创建的内存池异步申请指定大小的内存，返回地址供后续使用；试验特性。
- [aclrtMemPoolFreeAsync](aclrt_mem_pool_free_async.md)：在指定 Stream 上将内存归还池中以供复用，不释放底层物理内存；试验特性。
- [aclrtMemPoolTrimTo](aclrt_mem_pool_trim_to.md)：释放池中空闲物理内存，按 minBytesToKeep 指定保留大小；优先于 RELEASE_THRESHOLD 设置，属于试验特性。

## Device 变量内存操作

- [aclrtGetSymbolAddress](aclrt_get_symbol_address.md)：C 接口以 __gm__ 变量的符号地址查询实际 Device 地址，仅用于 Ascend C 毕昇混合编译，地址仅对当前 Device 有效。
- [aclrtGetSymbolSize](aclrt_get_symbol_size.md)：C 接口以 Device 变量的符号地址查询其占用字节数，沿用 GetSymbolAddress 的 Ascend C 混合编译约束。
- [aclrtMemcpyFromSymbol](aclrt_memcpy_from_symbol.md)：C 接口按符号地址及偏移，将 Device 变量同步复制到 Host；仅支持 D2H 或 DEFAULT，offset+count 不得越过变量大小。
- [aclrtMemcpyFromSymbolAsync](aclrt_memcpy_from_symbol_async.md)：C 接口按符号地址及偏移，在 Stream 上读取 Device 变量到 Host；Host 锁页内存下异步，非锁页下同步返回。
- [aclrtMemcpyToSymbol](aclrt_memcpy_to_symbol.md)：C 接口按符号地址及偏移，将 Host 数据同步写入 Device 变量；仅支持 H2D 或 DEFAULT，沿用混合编译符号访问约束。
- [aclrtMemcpyToSymbolAsync](aclrt_memcpy_to_symbol_async.md)：C 接口按符号地址及偏移，在 Stream 上将 Host 数据写入 Device 变量；Host 锁页内存下异步，非锁页下同步返回。
