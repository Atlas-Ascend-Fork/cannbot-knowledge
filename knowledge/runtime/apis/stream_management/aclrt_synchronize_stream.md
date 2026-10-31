---
type: API
title: aclrtSynchronizeStream
description: "C 单参数接口阻塞 Host 当前线程，等待指定 Stream 任务完成；读取同一流的异步结果前使用，需限时等待时改用 WithTimeout。"
tags:
- task.lookup
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/common/error_codes_inner.h
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-31T01:13:30Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSynchronizeStream

## 功能说明

阻塞 Host 侧当前线程，直到指定 Stream 中的所有任务都完成。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamSynchronize(stream)` 到 RTS 层；仅当其返回 `RT_ERROR_NONE` 时，本接口返回 `ACL_SUCCESS`。
- 对 `ACL_ERROR_RT_END_OF_SEQUENCE`、`ACL_ERROR_RT_MODEL_ABORT_NORMAL`、`ACL_ERROR_RT_AICORE_OVER_FLOW`、`ACL_ERROR_RT_AIVEC_OVER_FLOW`、`ACL_ERROR_RT_OVER_FLOW`、`ACL_ERROR_RT_SOCKET_CLOSE`，固定实现会记录 INFO 日志，随后仍通过 `ACL_GET_ERRCODE_RTS(rtErr)` 原样返回对应的非零状态码，不会转换为 `ACL_SUCCESS`。

## 函数原型

```c
aclError aclrtSynchronizeStream(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 `ACL_SUCCESS`（0）表示成功；RTS 返回非零状态时，该状态码原样返回。上述特殊状态即使记录 INFO 日志，也不会转换为 `ACL_SUCCESS`。

## 约束说明

- ACL_STREAM_PERSISTENT、ACL_STREAM_DEVICE_USE_ONLY、ACL_STREAM_CPU_SCHEDULE 类型的 Stream 不触发业务处理，直接返回成功。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L180)
- [`0_quickstart/4_custom_kernel_launch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/4_custom_kernel_launch/main.cpp#L74)
- [`1_basic_features/device/0_device_normal/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/0_device_normal/main.cpp#L125)

## 配套 API 与常见组合

- [aclrtMemcpyAsync](../memory_management/aclrt_memcpy_async.md)——异步拷贝下发后用本接口等待其在同一 Stream 上真正完成，再读取目标数据
- [aclrtSynchronizeStreamWithTimeout](aclrt_synchronize_stream_with_timeout.md)——需要防止任务挂死导致无限阻塞时，用带超时的变体替代
- [aclrtStreamQuery](aclrt_stream_query.md)——只需非阻塞查询 Stream 是否完成而非等待时改用该接口
