---
type: API
title: aclrtDestroyStream
description: 销毁 Stream，等待任务完成后销毁。
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
updated_at: '2026-10-29T08:46:01Z'
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

# aclrtDestroyStream

## 功能说明

销毁通过 [aclrtCreateStream](aclrt_create_stream.md) 或 [aclrtCreateStreamWithConfig](aclrt_create_stream_with_config.md) 创建的 Stream。若 Stream 上有未完成的任务，等待任务完成后再销毁。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamDestroy(stream)` 到 RTS 层；RTS 等待该 Stream 上所有已下发任务完成后再释放内部资源。

## 函数原型

```c
aclError aclrtDestroyStream(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 待销毁的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 销毁前建议先调用 [aclrtSynchronizeStream](aclrt_synchronize_stream.md) 确保任务完成。
- 需确保该 Stream 在当前 Context 下且其他接口未使用该 Stream。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L220)
- [`0_quickstart/4_custom_kernel_launch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/4_custom_kernel_launch/main.cpp#L96)
- [`1_basic_features/device/0_device_normal/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/0_device_normal/main.cpp#L141)

## 配套 API 与常见组合

- [aclrtCreateStream](aclrt_create_stream.md)——与创建配对；每个显式创建的 Stream 都应在资源回收阶段销毁
- [aclrtDestroyStreamForce](aclrt_destroy_stream_force.md)——需要不等待未完成任务立即释放时，用强制销毁替代
- [aclrtSynchronizeStream](aclrt_synchronize_stream.md)——普通销毁会隐式等待任务完成，提前显式同步可先暴露任务错误
