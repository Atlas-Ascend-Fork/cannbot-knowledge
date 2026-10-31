# 运行时配置 API

CANN Runtime 初始化/去初始化与运行时配置接口：aclInit 家族、系统参数与 Device/Stream 资源限制。

- [aclInit](acl_init.md)：初始化 ACL 环境，进程级引用计数，重复调用返回 ACL_ERROR_REPEAT_INITIALIZE。
- [aclFinalize](acl_finalize.md)：去初始化，直接清空初始化引用计数并释放进程内 acl 资源。
- [aclFinalizeReference](acl_finalize_reference.md)：按引用计数去初始化，计数归零才真正释放资源。
- [aclInitCallbackRegister](acl_init_callback_register.md)：注册初始化回调函数。
- [aclInitCallbackUnRegister](acl_init_callback_un_register.md)：取消注册初始化回调函数。
- [aclFinalizeCallbackRegister](acl_finalize_callback_register.md)：注册去初始化回调函数。
- [aclFinalizeCallbackUnRegister](acl_finalize_callback_un_register.md)：取消注册去初始化回调函数。
- [aclrtSetSysParamOpt](aclrt_set_sys_param_opt.md)：设置当前进程中的运行时参数值（进程作用域）。
- [aclrtGetSysParamOpt](aclrt_get_sys_param_opt.md)：获取当前进程中的运行时参数值。
- [aclrtGetDeviceResLimit](aclrt_get_device_res_limit.md)：获取当前进程的 Device 资源限制。
- [aclrtSetDeviceResLimit](aclrt_set_device_res_limit.md)：设置当前进程的 Device 资源限制。
- [aclrtResetDeviceResLimit](aclrt_reset_device_res_limit.md)：重置当前进程的 Device 资源限制。
- [aclrtGetStreamResLimit](aclrt_get_stream_res_limit.md)：获取指定 Stream 的 Device 资源限制。
- [aclrtSetStreamResLimit](aclrt_set_stream_res_limit.md)：设置指定 Stream 的 Device 资源限制。
- [aclrtResetStreamResLimit](aclrt_reset_stream_res_limit.md)：重置指定 Stream 的 Device 资源限制。
- [aclrtUseStreamResInCurrentThread](aclrt_use_stream_res_in_current_thread.md)：在当前线程中使用指定 Stream 上的 Device 资源限制。
- [aclrtUnuseStreamResInCurrentThread](aclrt_unuse_stream_res_in_current_thread.md)：在当前线程中取消使用指定 Stream 上的 Device 资源限制。
- [aclrtGetResInCurrentThread](aclrt_get_res_in_current_thread.md)：获取当前线程可使用的 Device 资源。
- [aclGetCannAttribute](acl_get_cann_attribute.md)：查询运行环境是否支持指定的 CANN 特性。
- [aclGetCannAttributeList](acl_get_cann_attribute_list.md)：查询运行环境中 CANN 软件和 AI 处理器支持的特性列表。
