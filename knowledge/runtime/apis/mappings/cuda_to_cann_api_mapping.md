---
type: API
title: CUDA 到 CANN Runtime API 映射与适配边界
description: 按设备、内存、流、事件、IPC、执行与 Graph 等模块整理 CUDA Runtime/Driver 到 CANN 的候选 API，保留组合、条件支持、兼容层差异和未映射范围。
tags:
- task.migration
- task.lookup
- topic.implementation.api_layer
status: draft
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/references/api_support_table.md
  role: primary
- resource: https://gitcode.com/cann/runtime/blob/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/assets/src/cann_compat_memory_copy.h
  role: implementation
- resource: https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/assets/src/cann_compat_cu_extra.h
  role: implementation
created_at: '2026-11-02T08:28:28Z'
updated_at: '2026-11-05T08:26:13Z'
platforms: []
aliases:
- CUDA API 映射
- CUDA to CANN Runtime
---

# CUDA 到 CANN Runtime API 映射与适配边界

## 适用范围与证据

本卡用于从 CUDA Runtime（`cuda*`）或 CUDA Driver（`cu*`）入口查找 CANN 主机侧候选 API，覆盖固定源表的设备、内存、流、事件、IPC、二进制、执行、Profiling、错误、版本、Graph、VMM 及未支持项。源技术为 CUDA，目标技术为 CANN Runtime；具体调用仍须区分公开 C 接口、C++ 扩展和迁移兼容层。

主来源为 `cann/cannbot-skills` 的 `runtime/runtime_migration/references/api_support_table.md`，固定到 `master` 在本次读取时的提交 `03cbbb9976901654d1fb27edb923bcd1b771f9bb`。下表提炼候选关系和限制，不沿用原表的成功勾选作为本卡的验证结果。Mock、内部存储、fallback、忽略参数和条件跳过均属于迁移项目的实现选择，不构成原生 CANN 等价契约。

源表没有为整张映射声明统一的芯片范围，因此本卡保持 `draft`、`platforms: []`；各链接卡的产品范围不能取并集后当作整卡支持范围。源表提及的 CUDA Runtime 13.2+、CANN 9.1.0+ 仅约束对应条目，不代表本卡全部接口的最低版本。Git 提交也不等于 SDK 发行版本。本次未编译兼容层、运行 CUDA/CANN 用例或进行 Device 验证。

表中的“候选”表示源表列出的调查入口；“组合”“兼容层”“条件”“未映射”分别保留不同的证据强度。原表没有列出的接口保持未知，不从名称拼接替代接口。“未映射”仅描述该固定迁移项目的范围，不外推为 CANN 所有版本都没有相关能力。

## 设备管理

| CUDA 入口 | CANN 候选或处理路线 | 适配边界 |
|---|---|---|
| `cudaGetDeviceCount` | [aclrtGetDeviceCount](../device_management/aclrt_get_device_count.md) | 候选：设备数量与设备 ID 使用目标接口约定。 |
| `cudaSetDevice` / `cudaGetDevice` | [aclrtSetDevice](../device_management/aclrt_set_device.md) / [aclrtGetDevice](../device_management/aclrt_get_device.md) | 候选：核对初始化、当前设备及 Context。 |
| `cudaGetDeviceProperties` | [aclrtGetDeviceInfo](../device_management/aclrt_get_device_info.md) | 候选：不能直接复用 CUDA 属性结构。 |
| `cudaDeviceGetAttribute` | Mock | 兼容层：返回的 CUDA 属性不证明目标硬件具有对应能力。 |
| `cudaDeviceSynchronize` | [aclrtSynchronizeDevice](../cpp_extension_apis/aclrt_synchronize_device.md) | 候选：本库同名入口是带 timeout 的 C++ 封装，C 程序须另核对 `aclrtSynchronizeDeviceWithTimeout`。 |
| `cudaDeviceReset` | [aclrtResetDeviceForce](../device_management/aclrt_reset_device_force.md) | 源表选择强制 Reset；不能无条件替换成普通 [aclrtResetDevice](../device_management/aclrt_reset_device.md)。 |
| `cudaSetDeviceFlags` / `cudaGetDeviceFlags` | 兼容层保存/读取 flags | 内部状态不证明 flags 对设备产生 CUDA 同等效果。 |
| `cudaDeviceSetLimit` / `cudaDeviceGetLimit` | [aclrtDeviceSetLimit](../device_management/aclrt_device_set_limit.md) / [aclrtDeviceGetLimit](../device_management/aclrt_device_get_limit.md) | 条件：源表仅映射 stack size、printf FIFO，其余 limit 返回 `cudaErrorUnsupportedLimit`。 |
| `cudaDeviceGetHostAtomicCapabilities` | [aclrtDeviceGetHostAtomicCapabilities](../device_management/aclrt_device_get_host_atomic_capabilities.md) | 条件：源表对空输出、零 count、非法 operation 做错误转换。 |
| `cudaDeviceGetP2PAtomicCapabilities` | [aclrtDeviceGetP2PAtomicCapabilities](../device_management/aclrt_device_get_p2p_atomic_capabilities.md) | 条件：同设备 src/dst 被兼容层拒绝；跨设备仍依赖设备数和拓扑。 |
| `cudaDeviceGetCacheConfig` / `cudaDeviceSetCacheConfig` | Mock / 内部存储 | 兼容层：查询或保存配置不等于实际改变 Cache 策略。 |
| `cudaDeviceGetStreamPriorityRange` | [aclrtDeviceGetStreamPriorityRange](../device_management/aclrt_device_get_stream_priority_range.md) | 候选：转换优先级的取值和含义。 |
| `cudaDeviceCanAccessPeer` | [aclrtDeviceCanAccessPeer](../device_management/aclrt_device_can_access_peer.md) | 条件：先查询能力，不能从设备数量推断 P2P 可达性。 |
| `cudaDeviceEnablePeerAccess` / `cudaDeviceDisablePeerAccess` | [aclrtDeviceEnablePeerAccess](../device_management/aclrt_device_enable_peer_access.md) / `aclrtDeviceDisablePeerAccess` | 条件：启用方向是当前设备到 peer；源表要求 enable flags 为 0，产品和拓扑另核对。 |

## 内存管理

### 分配、注册和属性

| CUDA 入口 | CANN 候选或处理路线 | 适配边界 |
|---|---|---|
| `cudaMalloc` / `cudaFree` | [aclrtMalloc](../memory_management/aclrt_malloc.md) / [aclrtFree](../memory_management/aclrt_free.md) | 候选：核对分配策略及未完成任务的内存生命周期。 |
| `cudaMallocPitch` | `aclrtMalloc` 加布局管理 | 组合：线性分配不自动提供等价 pitch，调用方须处理对齐和行距。 |
| `cudaMallocHost` / `cudaFreeHost` | [aclrtMallocHost](../memory_management/aclrt_malloc_host.md) / [aclrtFreeHost](../memory_management/aclrt_free_host.md) | 候选：Host 分配与 Device 地址映射需分开核对。 |
| `cudaHostAlloc` | 源表列 `aclrtMallocHostAndRegister`，或分配与 [aclrtHostRegisterV2](../memory_management/aclrt_host_register_v2.md) 组合 | 条件：mapped flags 需转换；源表还描述旧版本使用页对齐 Host 内存注册的路线，见下文冲突说明。 |
| `cudaHostRegister` / `cudaHostUnregister` | `aclrtHostRegisterV2` / [aclrtHostUnregister](../memory_management/aclrt_host_unregister.md) | 条件：default 对应 pinned，mapped 对应 mapped+pinned；不能直接传 CUDA flags 数值。 |
| `cudaHostGetDevicePointer` | [aclrtHostGetDevicePointer](../memory_management/aclrt_host_get_device_pointer.md) | 条件：源表以已建立 mapped Host 注册为前提。 |
| `cudaHostGetFlags` | [aclrtPointerGetAttributes](../memory_management/aclrt_pointer_get_attributes.md) 加兼容 flags | 兼容层：源表成功路径返回 `cudaHostAllocDefault`，不能恢复原始 CUDA flags。 |
| `cudaMemGetInfo` | [aclrtGetMemInfo](../memory_management/aclrt_get_mem_info.md) | 候选：核对查询的内存类别及容量单位。 |
| `cudaPointerGetAttributes` | `aclrtPointerGetAttributes` | 候选：逐字段适配属性，不重解释结构体。 |

Host 注册须特别保留版本差异：固定 Runtime 提交 `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的公开 `acl_rt.h` 未找到 `aclrtMallocHostAndRegister` 声明，不能据迁移表认定该提交已提供它，也不能据旧头文件否定后续版本。源表写出的 `aclrtMallocHost` + `aclrtHostRegisterV2` 还需与目标内存来源核对：本库注册卡限定 `ACL_HOST_REG_PINNED` 用于非锁页内存，不能机械地对已锁页分配再套 PINNED。

### 拷贝、初始化和设备符号

| CUDA 入口 | CANN 候选或处理路线 | 适配边界 |
|---|---|---|
| `cudaMemcpy` / `cudaMemcpyAsync` | [aclrtMemcpy](../memory_management/aclrt_memcpy.md) / [aclrtMemcpyAsync](../memory_management/aclrt_memcpy_async.md) | 候选：核对目标容量、长度、方向和 stream 完成时机。 |
| `cudaMemcpy2D` / `cudaMemcpy2DAsync` | [aclrtMemcpy2d](../memory_management/aclrt_memcpy2d.md) / [aclrtMemcpy2dAsync](../memory_management/aclrt_memcpy2d_async.md) | 候选：目标名称使用小写 `2d`；分别核对源/目标 pitch、宽高。 |
| `cudaMemcpy3D` / `cudaMemcpy3DAsync` | 按 slice 和方向分流：H2D/D2H 调用 `aclrtMemcpy2d` / `aclrtMemcpy2dAsync`，D2D 逐行调用 `aclrtMemcpy` / `aclrtMemcpyAsync`，H2H 逐行走 Host copy | 组合：同步 `aclrtMemcpy2d` 不接受 D2D；仅支持 linear pitched pointer，array/texture 3D 返回未支持，异步任务使用同一 stream。 |
| `cudaMemcpy3DPeer` / `cudaMemcpy3DPeerAsync` | 转换为 D2D 参数后，按 slice、逐行调用 `aclrtMemcpy` / `aclrtMemcpyAsync` | 条件：固定兼容实现忽略 `srcDevice` / `dstDevice`，不负责切换 Device；仅支持 linear pitched pointer，跨设备成功仍依赖目标 P2P、Context 与拓扑条件。 |
| `cudaMemcpyPeer` / `cudaMemcpyPeerAsync` | `aclrtMemcpy` / `aclrtMemcpyAsync` 的 `ACL_MEMCPY_DEVICE_TO_DEVICE` 路线 | 条件：源表仅报告同步同设备路径已验证；异步跨设备条目限定同一 PCIe Switch。该验证不是本次执行结果。 |
| `cudaMemcpyToSymbol` / `cudaMemcpyToSymbolAsync` | [aclrtMemcpyToSymbol](../memory_management/aclrt_memcpy_to_symbol.md) / [aclrtMemcpyToSymbolAsync](../memory_management/aclrt_memcpy_to_symbol_async.md) | 条件：兼容层的 C++ Host fallback symbol 异步路径立即完成，不等于设备任务时序。 |
| `cudaMemcpyFromSymbol` / `cudaMemcpyFromSymbolAsync` | [aclrtMemcpyFromSymbol](../memory_management/aclrt_memcpy_from_symbol.md) / [aclrtMemcpyFromSymbolAsync](../memory_management/aclrt_memcpy_from_symbol_async.md) | 条件：同样区分设备符号与 Host fallback。 |
| `cudaGetSymbolAddress` / `cudaGetSymbolSize` | [aclrtGetSymbolAddress](../memory_management/aclrt_get_symbol_address.md) / [aclrtGetSymbolSize](../memory_management/aclrt_get_symbol_size.md) | 条件：Host fallback 的 size 是兼容层 backing size。 |
| `cudaMemcpyBatchAsync` | [aclrtMemcpyBatchAsyncV2](../memory_management/aclrt_memcpy_batch_async_v2.md) 或逐项 `aclrtMemcpyAsync` | 条件：源表注明 CUDA Runtime 13.2+、CANN 9.1.0+；根据指针属性/location hint 选择方向，原生 batch 不可用时走兼容层 fallback。 |
| `cudaMemcpyWithAttributesAsync` | `aclrtMemcpyAsync` | 兼容层：源表忽略 access-order/location hint，只使用 CANN default copy kind。 |
| `cudaMemcpy3DBatchAsync` | 按 op、slice 调用 `aclrtMemcpy2dAsync` | 组合：pointer operand 路线；array operand 未映射。 |
| `cudaMemcpy3DWithAttributesAsync` | 单 op 按 slice 调用 `aclrtMemcpy2dAsync` | 条件：pointer operand，flags 仅允许 0。 |
| `cudaMemset` / `cudaMemsetAsync` | [aclrtMemset](../memory_management/aclrt_memset.md) / [aclrtMemsetAsync](../memory_management/aclrt_memset_async.md) | 候选：核对填充值、容量、长度与异步完成。 |
| `cuMemsetD32Async` | [aclrtMemsetD32Async](../memory_management/aclrt_memset_d32_async.md) | Driver 候选：保留 D32 写入单位，不能按字节填充处理。 |
| `cudaMemset2D` / `cudaMemset2DAsync` | 逐行 `aclrtMemset` / `aclrtMemsetAsync` | 组合：由调用方管理行距与提交次序。 |
| `cudaMemset3D` / `cudaMemset3DAsync` | 逐 slice、逐行填充 | 组合：仅 linear pitched pointer；异步任务保持在同一 stream。 |

### 托管内存 UVM

以下均为产品 UVM 能力约束下的候选，不能推导所有 CANN 产品都支持托管内存。

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaMallocManaged` | [aclrtMemAllocManaged](../memory_management/aclrt_mem_alloc_managed.md) | 源表只接受 `cudaMemAttachGlobal`。 |
| `cudaMemAdvise` | [aclrtMemManagedAdvise](../memory_management/aclrt_mem_managed_advise.md) | 显式适配 advice 和 device/location。 |
| `cudaMemPrefetchAsync` / `cudaMemPrefetchAsync_v2` | [aclrtMemManagedPrefetchAsync](../memory_management/aclrt_mem_managed_prefetch_async.md) | 分开处理 device-id 与 location 形态；flags 为 0，完成需同步 stream。 |
| `cudaMemRangeGetAttribute` / `cudaMemRangeGetAttributes` | [aclrtMemManagedGetAttr](../memory_management/aclrt_mem_managed_get_attr.md) / [aclrtMemManagedGetAttrs](../memory_management/aclrt_mem_managed_get_attrs.md) | 源表只列 read-mostly、preferred-location、accessed-by、last-prefetch-location 基础枚举。 |
| `cudaMemPrefetchBatchAsync` | [aclrtMemManagedPrefetchBatchAsync](../memory_management/aclrt_mem_managed_prefetch_batch_async.md) | flags 为 0，仍受产品能力限制。 |

## Stream 与 Event

### Stream 常规操作

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaStreamCreate` | [aclrtCreateStream](../stream_management/aclrt_create_stream.md) | 区分公开 C 与 C++ 同名入口。 |
| `cudaStreamCreateWithFlags` / `cudaStreamCreateWithPriority` | [aclrtCreateStreamWithConfig](../stream_management/aclrt_create_stream_with_config.md) | 转换 flags，核对目标优先级范围。 |
| `cudaStreamDestroy` | [aclrtDestroyStream](../stream_management/aclrt_destroy_stream.md) | 核对待完成任务与所属 Context。 |
| `cudaStreamSynchronize` / `cudaStreamQuery` | [aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md) / [aclrtStreamQuery](../stream_management/aclrt_stream_query.md) | 分别对应 Host 等待与状态查询。 |
| `cudaStreamWaitEvent` | [aclrtStreamWaitEvent](../event_management/aclrt_stream_wait_event.md) | 保留 stream 中的依赖关系，不用 Host 等待代替。 |
| `cudaStreamGetId` / `cudaStreamGetPriority` / `cudaStreamGetFlags` | [aclrtStreamGetId](../stream_management/aclrt_stream_get_id.md) / [aclrtStreamGetPriority](../stream_management/aclrt_stream_get_priority.md) / [aclrtStreamGetFlags](../stream_management/aclrt_stream_get_flags.md) | 输出类型、优先级和 flags 需按目标定义解释。 |
| `cudaStreamSetAttribute` / `cudaStreamGetAttribute` | [aclrtSetStreamAttribute](../stream_management/aclrt_set_stream_attribute.md) / [aclrtGetStreamAttribute](../stream_management/aclrt_get_stream_attribute.md) | 兼容层将 `cudaStreamAttrID` / `cudaStreamAttrValue` 按 CANN `aclrtStreamAttr` / `aclrtStreamAttrValue` 直通；不能由此认定同名属性语义相同。 |

### Event 操作

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaEventCreate` / `cudaEventCreateWithFlags` | [aclrtCreateEvent](../event_management/aclrt_create_event.md) / [aclrtCreateEventExWithFlag](../event_management/aclrt_create_event_ex_with_flag.md) | 区分计时用途和同步用途，逐项转换 flags。 |
| `cudaEventDestroy` / `cudaEventRecord` | [aclrtDestroyEvent](../event_management/aclrt_destroy_event.md) / [aclrtRecordEvent](../event_management/aclrt_record_event.md) | 保留记录、复用、销毁的顺序。 |
| `cudaEventRecordWithFlags` | [aclrtRecordEventWithFlag](../event_management/aclrt_record_event_with_flag.md) | 条件：源表旧头文件缺声明时仅将 default flag 回退到 `aclrtRecordEvent`，external flag 返回未支持。 |
| `cudaEventSynchronize` / `cudaEventQuery` | [aclrtSynchronizeEvent](../event_management/aclrt_synchronize_event.md) / [aclrtQueryEventStatus](../event_management/aclrt_query_event_status.md) | 区分等待完成和查询状态。 |
| `cudaEventElapsedTime` | [aclrtEventElapsedTime](../event_management/aclrt_event_elapsed_time.md) | 核对计时 Event 的模式、完成条件和时间单位。 |

## 跨进程 IPC

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaIpcGetMemHandle` | [aclrtIpcMemGetExportKey](../memory_management/aclrt_ipc_mem_get_export_key.md) | 条件：源表要求页对齐共享范围，部分产品可能拒绝。 |
| `cudaIpcOpenMemHandle` | [aclrtIpcMemImportByKey](../memory_management/aclrt_ipc_mem_import_by_key.md) | 源表建议使用 exec 子进程验证，避免 fork 继承运行时 Context。 |
| `cudaIpcCloseMemHandle` | [aclrtIpcMemClose](../memory_management/aclrt_ipc_mem_close.md) | 导入方先关闭，导出方再释放底层内存。 |
| `cudaIpcGetEventHandle` / `cudaIpcOpenEventHandle` | [aclrtIpcGetEventHandle](../event_management/aclrt_ipc_get_event_handle.md) / [aclrtIpcOpenEventHandle](../event_management/aclrt_ipc_open_event_handle.md) | 核对目标 IPC Event 的句柄与生命周期。 |

源表以 opaque handle 和共享内存传递描述该 IPC 路线，不能将其当成 POSIX fd 或与 CUDA handle 直接互传。下文 VMM 的 shareable handle 是另一组接口，源表明确有 POSIX FD 表示转换，不能将两处句柄约定合并。

## 库、模块与 Kernel 执行

### 二进制加载与查询

| CUDA 或迁移表入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaLibraryLoadFromFile` / `cuModuleLoad` | [aclrtBinaryLoadFromFile](../kernel_loading_and_execution/aclrt_binary_load_from_file.md) | 目标须能识别输入二进制，不表示 CUDA cubin/PTX 可以直接执行。 |
| `cudaLibraryLoadData` / `cuModuleLoadData` | [aclrtBinaryLoadFromData](../kernel_loading_and_execution/aclrt_binary_load_from_data.md) | 核对二进制格式、数据长度及所有权。 |
| `cudaLibraryUnload` / `cuModuleUnload` | [aclrtBinaryUnLoad](../kernel_loading_and_execution/aclrt_binary_un_load.md) | 源表前一条写成 `aclrtBinaryUnload`、后一条写成 `aclrtBinaryUnLoad`；本库固定头文件声明为后者。 |
| `cuModuleGetFunction` | [aclrtBinaryGetFunction](../kernel_loading_and_execution/aclrt_binary_get_function.md) | 核对目标函数名与句柄生命周期。 |
| 源表的 `cudaLibraryGetFunction` | `aclrtBinaryGetFunction` | 仅保留迁移项目使用的入口名；本次未核验该名称为 NVIDIA 正式声明，不能据此生成原生 CUDA 调用。 |
| `cudaLibraryGetGlobal` | [aclrtBinaryGetGlobal](../kernel_loading_and_execution/aclrt_binary_get_global.md) | 条件：源表标注 CANN 9.1.0+，目标发行版本另核对。 |

### Host 回调、函数属性与启动

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cudaLaunchHostFunc` / `cudaLaunchHostFunc_v2` | [aclrtLaunchHostFunc](../execution_control/aclrt_launch_host_func.md) | 兼容层把空回调处理为成功 no-op，并忽略 v2 syncMode；不能归入原生接口约束。 |
| `cudaFuncGetAttributes` | [aclrtGetFunctionAttribute](../kernel_loading_and_execution/aclrt_get_function_attribute.md) | 转换 CANN 属性到 CUDA 属性结构，不能整体照搬。 |
| `cudaFuncGetName` | [aclrtGetFunctionName](../kernel_loading_and_execution/aclrt_get_function_name.md) | 源表兼容层返回内部静态缓冲区指针，需核对生命周期。 |
| `cudaFuncGetParamCount` / `cudaFuncGetParamInfo` | [aclrtFunctionGetParamCount](../kernel_loading_and_execution/aclrt_function_get_param_count.md) / [aclrtFunctionGetParamInfo](../kernel_loading_and_execution/aclrt_function_get_param_info.md) | 查询参数个数与 offset/size；源表不接受两个参数信息输出同时为空。 |
| `cudaLaunchKernel` | [aclrtLaunchKernelWithHostArgs](../kernel_loading_and_execution/aclrt_launch_kernel_with_host_args.md) / [aclrtLaunchKernelWithArgsArray](../kernel_loading_and_execution/aclrt_launch_kernel_with_args_array.md) / [aclrtLaunchSIMTKernelWithArgsArray](../kernel_loading_and_execution/aclrt_launch_simt_kernel_with_args_array.md) / [aclrtLaunchSIMTKernelWithHostArgs](../kernel_loading_and_execution/aclrt_launch_simt_kernel_with_host_args.md) | 条件：仅 CANN 可识别的 function/kernel handle；源表默认走参数数组，CUDA `<<<>>>` 则另走 Host fallback。 |
| `cudaLaunchKernelEx` | `aclrtLaunchKernelWithHostArgs` | 组合：按参数个数、offset 和 size 将 `void **args` 打包为 HostArgs。 |

这些启动映射不提供 CUDA Kernel 源码、线程组织、内建变量或二进制的等价迁移；须独立处理目标内核编程模型。

## Stream Capture 与 Graph / Model RI

该组映射中的 CANN Model RI 能力按源表视为试验特性；有明确说明的接口不可用于生产，且后续版本可能变化。Graph 对象、执行实例、stream/task 与 conditional task 的关系必须重新核对，不承诺完整 CUDA Graph 语义。

| CUDA 入口 | CANN 候选或处理路线 | 适配边界 |
|---|---|---|
| `cudaStreamBeginCapture` / `cudaStreamEndCapture` | [aclmdlRICaptureBegin](../model_running_instance_management/aclmdl_ri_capture_begin.md) / [aclmdlRICaptureEnd](../model_running_instance_management/aclmdl_ri_capture_end.md) | 条件：转换 capture mode，源表先拒绝非法模式。 |
| `cudaStreamBeginCaptureToGraph` | [aclmdlRICaptureToModelRIBegin](../model_running_instance_management/aclmdl_ri_capture_to_model_ri_begin.md) | 条件：捕获到已有 Model RI；源表明确不用于生产。 |
| `cudaStreamCaptureStatus` | `aclmdlRICaptureStatus` | 类型映射：显式转换 None、Active、Invalidated。 |
| `cudaStreamGetCaptureInfo` / `cudaStreamGetCaptureInfo_v3` / `cudaStreamIsCapturing` | [aclmdlRICaptureGetInfo](../model_running_instance_management/aclmdl_ri_capture_get_info.md) | 兼容层按参数个数适配 v2/v3 形态，不能直接复用声明。 |
| `cudaThreadExchangeStreamCaptureMode` | [aclmdlRICaptureThreadExchangeMode](../model_running_instance_management/aclmdl_ri_capture_thread_exchange_mode.md) | 转换线程 capture mode。 |
| `cudaGraphDebugDotPrint` | [aclmdlRIDebugJsonPrint](../model_running_instance_management/aclmdl_ri_debug_json_print.md) | 输出是 RI JSON，不保留 DOT 文件格式。 |
| `cudaGraphExecDestroy` | [aclmdlRIDestroy](../model_running_instance_management/aclmdl_ri_destroy.md) | 仅执行实例候选，不能扩大为 `cudaGraphDestroy` 的对象销毁语义。 |
| `cudaGraphConditionalHandleCreate` | [aclmdlRICondHandleCreate](../model_running_instance_management/aclmdl_ri_cond_handle_create.md) | 条件：试验接口，源表明确不用于生产。 |
| `cudaGraphAddNode` 的 `cudaGraphNodeTypeConditional` | [aclmdlRIAddCondTask](../model_running_instance_management/aclmdl_ri_add_cond_task.md) | 仅 conditional node 特例；通用 node 仍属源表未支持项。 |
| `cudaGraphGetNodes` | [aclmdlRIGetStreams](../model_running_instance_management/aclmdl_ri_get_streams.md) + [aclmdlRIGetTasksByStream](../model_running_instance_management/aclmdl_ri_get_tasks_by_stream.md) | 组合：汇总 RI stream/task；不能不加验证地视为 CUDA 节点模型。 |
| `cudaGraphLaunch` | [aclmdlRIExecuteAsync](../model_running_instance_management/aclmdl_ri_execute_async.md) | 条件：异步执行的提交和完成分开核对。 |
| `cudaGraphSetConditional` | [aclmdlRICondHandleGetCondPtr](../model_running_instance_management/aclmdl_ri_cond_handle_get_cond_ptr.md) 后写条件值 | 组合：取得设备条件指针再写入，不能仅用 Host 查询代替；源表明确不用于生产。 |

## Driver VMM、Context 与 Stream value

| CUDA 入口 | CANN 候选 | 适配边界 |
|---|---|---|
| `cuMemAddressReserve` / `cuMemAddressFree` | [aclrtReserveMemAddress](../memory_management/aclrt_reserve_mem_address.md) / [aclrtReleaseMemAddress](../memory_management/aclrt_release_mem_address.md) | 预留和释放虚拟地址，区别于物理内存分配。 |
| `cuMemCreate` / `cuMemRelease` | [aclrtMallocPhysical](../memory_management/aclrt_malloc_physical.md) / [aclrtFreePhysical](../memory_management/aclrt_free_physical.md) | 核对分配属性、物理句柄与粒度。 |
| `cuMemMap` / `cuMemUnmap` | [aclrtMapMem](../memory_management/aclrt_map_mem.md) / [aclrtUnmapMem](../memory_management/aclrt_unmap_mem.md) | 地址预留、物理分配、映射、权限各是独立阶段。 |
| `cuMemGetAccess` / `cuMemSetAccess` | [aclrtMemGetAccess](../memory_management/aclrt_mem_get_access.md) / [aclrtMemSetAccess](../memory_management/aclrt_mem_set_access.md) | 条件：源表对不支持的产品/部分 access 错误作未支持处理；不能把跳过算作权限设置成功。 |
| `cuMemGetAllocationGranularity` | [aclrtMemGetAllocationGranularity](../memory_management/aclrt_mem_get_allocation_granularity.md) | 使用目标属性与粒度约定。 |
| `cuMemExportToShareableHandle` / `cuMemImportFromShareableHandle` | [aclrtMemExportToShareableHandleV2](../memory_management/aclrt_mem_export_to_shareable_handle_v2.md) / [aclrtMemImportFromShareableHandleV2](../memory_management/aclrt_mem_import_from_shareable_handle_v2.md) | 条件：POSIX FD 路线在 CUDA `int` 与 CANN `uint64_t` 间转换；源表要求 V2 导入通过 exec 子进程验收，不用同进程 export/import 代替。 |
| `cuMemRetainAllocationHandle` | [aclrtMemRetainAllocationHandle](../memory_management/aclrt_mem_retain_allocation_handle.md) | 核对句柄保留及后续释放配对。 |
| `cuCtxGetCurrent` / `cuCtxSetCurrent` | [aclrtGetCurrentContext](../context_management/aclrt_get_current_context.md) / [aclrtSetCurrentContext](../context_management/aclrt_set_current_context.md) | 仅当前 Context 操作，不自动提供 push/pop 栈。 |
| `cuDevicePrimaryCtxGetState` | [aclrtGetPrimaryCtxState](../context_management/aclrt_get_primary_ctx_state.md) | 状态查询不等于 primary Context retain。 |
| `cuStreamWriteValue32` | [aclrtValueWrite](../memory_management/aclrt_value_write.md) | 兼容层将 `uint32_t` 值零扩展为 `uint64_t` 后执行 64-bit 写入，不是原生 32-bit 等价替换；目标地址须 8 字节对齐并具有独占的 8 字节有效空间，`flags` 仅可使用目标接口接受的 0。 |
| `cudaOccupancyAvailableDynamicSMemPerBlock` | [aclrtFunctionGetAvailDynUbufPerBlock](../kernel_loading_and_execution/aclrt_function_get_avail_dyn_ubuf_per_block.md) | 查询目标动态 UBuf；源表仅对 CUDA numBlocks/blockSize 做合法性校验，不是 CUDA occupancy 模型。 |

## Profiling、错误与版本

| CUDA 入口 | CANN 候选或处理路线 | 适配边界 |
|---|---|---|
| `cudaProfilerStart` | [aclprofInit](../profiling_data_collection/aclprof_init.md) + [aclprofStart](../profiling_data_collection/aclprof_start.md) | 组合：需单独核对 Profiling 配置与生命周期。 |
| `cudaProfilerStop` | [aclprofStop](../profiling_data_collection/aclprof_stop.md) + [aclprofFinalize](../profiling_data_collection/aclprof_finalize.md) | 组合：停止采集后完成 Profiling 收尾。 |
| `cudaGetLastError` / `cudaPeekAtLastError` | [aclrtGetLastError](../exception_handling/aclrt_get_last_error.md) / [aclrtPeekAtLastError](../exception_handling/aclrt_peek_at_last_error.md) | 核对线程级参数，以及获取后是否清空错误状态。 |
| `cudaGetErrorName` | 兼容层错误表；未知项尝试 `aclGetRecentErrMsg` | 兼容层：未知项还可能落到 `cudaErrorUnknown`，不是原生错误码一一对应。 |
| `cudaGetErrorString` | `aclGetRecentErrMsg` 加本地文本包装 | 最近 ACL 错误消息不等于任意历史 CUDA 错误码的字符串。 |
| `cudaRuntimeGetVersion` | [aclsysGetVersionNum](../other_apis/aclsys_get_version_num.md) | 版本体系与编码需转换，不把 CANN 版本号解释成 CUDA 版本。 |

## 固定源表未提供映射的接口

以下为该迁移参考的未支持范围。同名兼容入口可能仅供编译并返回 not supported，不能用“可编译”替代运行验证。

| 类别 | CUDA 入口 | 本卡保留的边界 |
|---|---|---|
| SOMA 分配/释放 | `cudaMallocAsync`、`cudaFreeAsync` | 不用普通 malloc/free 替代后仍承诺 stream-ordered 语义。 |
| 内存池创建/销毁 | `cudaMemPoolCreate`、`cudaMemPoolDestroy`、`cudaMemPoolTrimTo` | 源表未映射池生命周期和 trim。 |
| 内存池属性/权限 | `cudaMemPoolSetAttribute`、`cudaMemPoolGetAttribute`、`cudaMemPoolSetAccess`、`cudaMemPoolGetAccess` | 源表的 `cudaMemPoolsetAttribute`、`cudaMemPoolsetAccess` 是另列拼写，不作为已核验的正式 API 名称。 |
| 内存池共享 | `cudaMemPoolExportPointer`、`cudaMemPoolExportToShareableHandle`、`cudaMemPoolImportFromShareableHandle`、`cudaMemPoolImportPointer` | VMM 或 IPC 的其他候选不能直接补齐池共享语义。 |
| Device 内存池 | `cudaDeviceGetDefaultMemPool`、`cudaDeviceGetMemPool`、`cudaDeviceSetMemPool` | 源表还列 `cudaMemGetDefaultMemPool`、`cudaMemGetMemPool`、`cudaMemSetMemPool`；仅记录源表拼写和未支持状态。 |
| UVM discard 扩展 | `cudaMemDiscardAndPrefetchBatchAsync`、`cudaMemDiscardBatchAsync`、`cuMemDiscardAndPrefetchBatchAsync`、`cuMemDiscardBatchAsync` | 与前文条件支持的基础 UVM 接口分开。 |
| Driver 指针批量属性/设置 | `cuPointerGetAttributes`、`cuPointerSetAttribute` | 单个 Runtime 属性查询不补齐该组语义。 |
| 函数属性/Cache 设置 | `cudaFuncSetAttribute`、`cuFuncSetCacheConfig` | 源表兼容入口返回未支持。 |
| Cooperative launch | `cudaLaunchCooperativeKernel` | 常规 Kernel 启动候选不提供该能力。 |
| Driver entry 查询 | `cudaGetDriverEntryPoint`、`cudaGetDriverEntryPointByVersion` | 不构造对应 CANN 入口。 |
| 通用 Graph 节点/依赖 | `cudaGraphAddNode`、`cudaGraphAddNode_v2`、`cudaGraphNodeGetDependencies` | 仅前文 conditional node 是例外。 |
| Graph 对象/实例化 | `cudaGraphDestroy`、`cudaGraphInstantiateWithFlags` | `aclmdlRIDestroy` 的执行实例候选不能扩大为对象语义。 |
| Occupancy 通用查询 | `cudaOccupancyMaxActiveBlocksPerMultiprocessor`、`cudaOccupancyMaxPotentialBlockSize` | 动态 UBuf 查询不等于 occupancy 计算。 |
| Capture 依赖更新 | `cudaStreamUpdateCaptureDependencies`、`cudaStreamUpdateCaptureDependencies_v2` | 开始/结束捕获不补齐依赖更新。 |
| Driver Context 栈/retain | `cuCtxPushCurrent`、`cuCtxPopCurrent`、`cuDevicePrimaryCtxRetain` | Set/Get 当前 Context 或状态查询不提供栈和引用持有语义。 |
| Green Context | `cuGreenCtxCreate`、`cuGreenCtxDestroy`、`cuCtxFromGreenCtx`、`cuDeviceGetDevResource`、`cuGreenCtxStreamCreate` | 固定源表无对应路线。 |
| Driver JIT / Link | `cuModuleLoadDataEx`、`cuLinkAddData` | 普通二进制加载不提供 PTX/JIT/link 兼容性。 |
| Multicast | `cuMulticastAddDevice`、`cuMulticastBindMem`、`cuMulticastCreate`、`cuMulticastUnbind` | 固定源表无对应路线。 |
| Tensor Map | `cuTensorMapEncodeTiled` | 固定源表无对应路线。 |
| Texture / Surface | 源表仅列 API 家族 | 源表建议调查普通内存配合自定义逻辑；属于工程重写线索，没有完整等价承诺。 |

## 使用与验证方法

1. 先确认实际 CUDA 入口层、目标产品、CUDA/CANN 发行版本与要保留的设计意图；从本表选择候选，不以同名或成功勾选判断等价。
2. 打开目标 API 卡及其固定来源，核对完整声明、C/C++、flags、容量/计数单位、句柄表示、Context/Device 归属、所有权与释放配对。目标 SDK 没有相应声明时保留版本缺口，不自行创造 API。
3. 对组合/fallback 路线另核对 pitch、迭代提交、错误传播和完成时机；对 P2P、IPC、UVM、VMM 核对产品能力与拓扑；对 Model RI 保留试验特性和生产限制。
4. 在实际 SDK 中编译最小用例，再按需要验证成功/异常路径、资源释放、异步同步点、跨进程与跨设备行为。只有实测后才记录实际产品、版本和结果；本卡本次仅完成来源整理及知识治理检查。

## 来源与后续入口

- [固定迁移支持表](https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/references/api_support_table.md)：候选关系、兼容层行为和未支持范围的主来源。
- [固定 3D 拷贝兼容实现](https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/assets/src/cann_compat_memory_copy.h)：按方向区分二维、逐行 D2D 与 Host copy 路线，并保留 Peer 参数处理边界。
- [固定 Driver 扩展兼容实现](https://gitcode.com/cann/cannbot-skills/blob/03cbbb9976901654d1fb27edb923bcd1b771f9bb/runtime/runtime_migration/assets/src/cann_compat_cu_extra.h)：`cuStreamWriteValue32` 到 64-bit `aclrtValueWrite` 的实际参数转换。
- [固定 Runtime 公开头文件](https://gitcode.com/cann/runtime/blob/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h)：仅用于上文 `aclrtBinaryUnLoad` 拼写和 `aclrtMallocHostAndRegister` 声明缺口的对照，不证明新版候选已在该提交全部存在。
- [Runtime API 模块导航](../index.md)：目标 API 的独立契约和适用范围入口；表中普通链接仅帮助进一步核验，不表示本次已逐张复核全部目标卡。
