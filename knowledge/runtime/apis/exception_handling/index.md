# 异常处理 API

异常回调注册、错误信息查询、UCE 修复及任务中止接口。

- [aclrtSetExceptionInfoCallback（已废弃）](aclrt_set_exception_info_callback_deprecated.md)：注册异常信息回调（旧接口，改用 Register/Unregister 系列）。
- [aclrtExceptionInfoCallbackRegister](aclrt_exception_info_callback_register.md)：注册异常信息回调函数。
- [aclrtExceptionInfoCallbackUnregister](aclrt_exception_info_callback_unregister.md)：取消注册异常信息回调函数。
- [aclrtGetTaskIdFromExceptionInfo](aclrt_get_task_id_from_exception_info.md)：从异常信息中获取任务 ID。
- [aclrtGetStreamIdFromExceptionInfo](aclrt_get_stream_id_from_exception_info.md)：从异常信息中获取 Stream ID。
- [aclrtGetThreadIdFromExceptionInfo](aclrt_get_thread_id_from_exception_info.md)：从异常信息中获取线程 ID。
- [aclrtGetDeviceIdFromExceptionInfo](aclrt_get_device_id_from_exception_info.md)：从异常信息中获取 Device ID。
- [aclrtGetErrorCodeFromExceptionInfo](aclrt_get_error_code_from_exception_info.md)：从异常信息中获取错误码。
- [aclrtPeekAtLastError](aclrt_peek_at_last_error.md)：查看上次错误（不清除）。
- [aclrtGetLastError](aclrt_get_last_error.md)：获取并清除上次错误。
- [aclrtGetMemUceInfo](aclrt_get_mem_uce_info.md)：查询内存 UCE 错误信息。
- [aclrtMemUceRepair](aclrt_mem_uce_repair.md)：修复内存 UCE 错误。
- [aclrtDeviceTaskAbort](aclrt_device_task_abort.md)：中止 Device 上的异常任务。
- [aclrtGetErrorVerbose](aclrt_get_error_verbose.md)：获取详细错误信息。
- [aclrtRepairError](aclrt_repair_error.md)：上报错误并触发修复流程。
- [aclrtSetDeviceTaskAbortCallback](aclrt_set_device_task_abort_callback.md)：注册任务中止回调函数。
