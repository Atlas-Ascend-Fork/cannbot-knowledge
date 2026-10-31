# Kernel 加载与执行 API

CANN Runtime Kernel 加载与执行接口：算子二进制加载、核函数查询、参数列表组装及 Kernel 启动。

## 二进制加载与卸载

- [aclrtBinaryLoadFromFile](aclrt_binary_load_from_file.md)：从文件加载并解析算子二进制，输出 binHandle。
- [aclrtBinaryLoadFromData](aclrt_binary_load_from_data.md)：从内存加载并解析算子二进制数据，输出 binHandle。
- [aclrtCreateBinary](aclrt_create_binary.md)：创建描述算子二进制信息的 aclrtBinary 数据。
- [aclrtDestroyBinary](aclrt_destroy_binary.md)：销毁通过 aclrtCreateBinary 创建的数据。
- [aclrtBinaryLoad](aclrt_binary_load.md)：解析加载算子二进制并拷贝至当前 Context 对应 Device。
- [aclrtBinaryUnLoad](aclrt_binary_un_load.md)：删除 binHandle 指向的算子二进制数据及 Device 上的拷贝。
- [aclrtBinarySetExceptionCallback](aclrt_binary_set_exception_callback.md)：注册算子执行异常回调函数。

## 核函数查询

- [aclrtBinaryGetFunction](aclrt_binary_get_function.md)：根据核函数名称获取核函数句柄。
- [aclrtBinaryGetFunctionByEntry](aclrt_binary_get_function_by_entry.md)：根据 Function Entry 获取核函数句柄（预留，暂不支持）。
- [aclrtBinaryGetFunctionCount](aclrt_binary_get_function_count.md)：获取算子二进制中核函数总数。
- [aclrtBinaryEnumerateFunctions](aclrt_binary_enumerate_functions.md)：获取算子二进制中指定数量的核函数句柄。
- [aclrtBinaryGetDevAddress](aclrt_binary_get_dev_address.md)：获取算子二进制在 Device 上的地址及大小。
- [aclrtBinaryGetGlobal](aclrt_binary_get_global.md)：获取 Device 侧全局变量的地址和大小。
- [aclrtGetFuncBySymbol](aclrt_get_func_by_symbol.md)：根据核函数名获取核函数句柄（混合编译场景）。
- [aclrtGetFunctionAddr](aclrt_get_function_addr.md)：获取 Device 侧算子起始地址。
- [aclrtGetFunctionSize](aclrt_get_function_size.md)：获取核函数代码段大小。
- [aclrtGetFunctionName](aclrt_get_function_name.md)：获取核函数名称。
- [aclrtGetFunctionAttribute](aclrt_get_function_attribute.md)：获取核函数属性信息。
- [aclrtFunctionGetBinary](aclrt_function_get_binary.md)：根据核函数句柄获取算子二进制句柄。
- [aclrtFunctionGetParamCount](aclrt_function_get_param_count.md)：获取核函数参数个数。
- [aclrtFunctionGetParamInfo](aclrt_function_get_param_info.md)：获取指定索引参数的信息（偏移和大小）。
- [aclrtFunctionGetAvailDynUbufPerBlock](aclrt_function_get_avail_dyn_ubuf_per_block.md)：获取每个 Block 可用的动态 UB buffer 大小。
- [aclrtRegisterCpuFunc](aclrt_register_cpu_func.md)：注册 AI CPU 算子信息。
- [aclrtGetArgsFromExceptionInfo](aclrt_get_args_from_exception_info.md)：从异常信息中获取算子执行参数。
- [aclrtGetFuncHandleFromExceptionInfo](aclrt_get_func_handle_from_exception_info.md)：从异常信息中获取核函数句柄。
- [aclrtGetHardwareSyncAddr](aclrt_get_hardware_sync_addr.md)：获取 Cube Core 与 Vector Core 之间的同步地址。

## 参数列表组装

- [aclrtKernelArgsInit](aclrt_kernel_args_init.md)：初始化参数列表（系统管理内存）。
- [aclrtKernelArgsInitByUserMem](aclrt_kernel_args_init_by_user_mem.md)：初始化参数列表（用户管理内存）。
- [aclrtKernelArgsGetMemSize](aclrt_kernel_args_get_mem_size.md)：根据 Kernel 和用户参数大小查询参数数据实际所需的存储字节数；用户参数逐项按 8 字节对齐后累计，句柄空间另行查询。
- [aclrtKernelArgsGetHandleMemSize](aclrt_kernel_args_get_handle_mem_size.md)：查询指定 Kernel 参数句柄对象所需的存储字节数，供用户管理参数内存时分配句柄空间；参数数据空间另用 GetMemSize 查询。
- [aclrtKernelArgsAppend](aclrt_kernel_args_append.md)：追加参数值到参数数据区域。
- [aclrtKernelArgsAppendPlaceHolder](aclrt_kernel_args_append_place_holder.md)：为 placeholder 参数占位。
- [aclrtKernelArgsGetPlaceHolderBuffer](aclrt_kernel_args_get_place_holder_buffer.md)：获取占位符指向的内存地址。
- [aclrtKernelArgsParaUpdate](aclrt_kernel_args_para_update.md)：更新已追加的参数值。
- [aclrtKernelArgsFinalize](aclrt_kernel_args_finalize.md)：标识参数组装完毕。

## Kernel 启动

- [aclrtLaunchKernel](aclrt_launch_kernel.md)：启动算子计算任务（参数在 Device 内存）。异步接口。
- [aclrtLaunchKernelV2](aclrt_launch_kernel_v2.md)：带配置信息启动算子计算任务（参数在 Device 内存）。异步接口。
- [aclrtLaunchKernelWithConfig](aclrt_launch_kernel_with_config.md)：使用参数列表句柄启动算子计算任务。异步接口。
- [aclrtLaunchKernelWithHostArgs](aclrt_launch_kernel_with_host_args.md)：使用 Host 参数启动算子计算任务。异步接口。
- [aclrtLaunchKernelWithArgsArray](aclrt_launch_kernel_with_args_array.md)：使用参数数组启动核函数计算任务。异步接口。
- [aclrtLaunchSIMTKernelWithArgsArray](aclrt_launch_simt_kernel_with_args_array.md)：使用参数数组启动 SIMT 核函数。异步接口。
- [aclrtLaunchSIMTKernelWithHostArgs](aclrt_launch_simt_kernel_with_host_args.md)：使用 Host 参数启动 SIMT 核函数。异步接口。
