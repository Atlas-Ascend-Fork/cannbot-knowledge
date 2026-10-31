# Context 管理 API

CANN Runtime Context 管理接口：Context 创建、销毁、切换及参数配置。

- [aclrtCreateContext](aclrt_create_context.md)：显式创建并绑定当前线程的 Context，自带默认 Stream；同一 Device 可有多个 Context，独立于 SetDevice 的默认 Context 引用计数。
- [aclrtDestroyContext](aclrt_destroy_context.md)：销毁显式创建的 Context，调用前须同步其 Stream；默认 Context 应通过 aclrtResetDevice 释放。
- [aclrtSetCurrentContext](aclrt_set_current_context.md)：切换当前线程使用的 Context，跨 Device 时随之切换 Device；多次设置以最后一次为准。
- [aclrtGetCurrentContext](aclrt_get_current_context.md)：查询当前线程最后绑定的 Context；线程未设置 Device 或 Context 时，返回的 Context 指针为空。
- [aclrtCtxSetSysParamOpt](aclrt_ctx_set_sys_param_opt.md)：设置 Context 级系统参数，如确定性、调试 Kernel 和强一致性；重复设置以最后一次为准，与进程级参数区分。
- [aclrtCtxGetSysParamOpt](aclrt_ctx_get_sys_param_opt.md)：查询当前 Context 的系统参数；无默认值，须先调用 aclrtCtxSetSysParamOpt，未设置时返回错误。
- [aclrtCtxGetCurrentDefaultStream](aclrt_ctx_get_current_default_stream.md)：获取当前 Context 隐式创建的默认 Stream；当前线程须已有有效 Context，不另建 Stream。
- [aclrtGetPrimaryCtxState](aclrt_get_primary_ctx_state.md)：查询指定 Device 的默认 Context 是否激活；active 返回 0 或 1，预留参数 flags 必须传 NULL。
- [aclrtCtxGetFloatOverflowAddr](aclrt_ctx_get_float_overflow_addr.md)：获取当前 Context 中保存饱和模式溢出标记的 Device 地址，作为 Workspace 参数传给 AI Core 算子。
