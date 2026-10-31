---
type: API
title: aclrtCreateStream
description: "C 单参数接口显式创建默认优先级的 Stream，作为任务下发队列；调用本接口不能指定 priority 或 flag。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
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

# aclrtCreateStream

## 功能说明

创建 Stream。若不显式创建，每个 Context 对应一个默认 Stream（最高优先级）。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamCreate(stream, RT_STREAM_PRIORITY_DEFAULT)` 到 RTS 层分配 Stream 内部资源。

## 函数原型

```c
aclError aclrtCreateStream(aclrtStream *stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输出 | Stream 的指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- Stream 最大数：950/A3/A2 为 1984，310p 为 1024，310b 为 512，910 为 2048。
- 多进程场景下接近上限时可能创建失败，建议分批创建或清理冗余 Stream。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L101)
- [`0_quickstart/4_custom_kernel_launch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/4_custom_kernel_launch/main.cpp#L48)
- [`1_basic_features/device/0_device_normal/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/0_device_normal/main.cpp#L22)

## 配套 API 与常见组合

- [aclrtMemcpyAsync](../memory_management/aclrt_memcpy_async.md)——创建出的 Stream 作为异步拷贝等任务的下发队列，拷贝完成时机由该 Stream 的后续同步决定
- [aclrtSynchronizeStream](aclrt_synchronize_stream.md)——阻塞等待本 Stream 上已下发任务全部完成，是读取异步结果前的必经同步
- [aclrtDestroyStream](aclrt_destroy_stream.md)——与创建配对，在资源回收阶段销毁；普通销毁会先等待任务完成
