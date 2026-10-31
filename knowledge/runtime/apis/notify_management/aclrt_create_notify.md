---
type: API
title: aclrtCreateNotify
description: 创建 Notify。支持通过 flag 指定 Host 或 Device 使用场景。不同型号单个 Device 支持的 Notify 数量不同。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/08_notify_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/notify.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtCreateNotify

## 功能说明

创建 Notify。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCreateNotifyImpl`（notify.cpp:25）对 notify 指针做空校验，通过 `rtsNotifyCreate(static_cast<rtNotify_t*>(notify), flag)` 创建。flag 仅影响 Notify 的使用场景（Host 或 Device），不改变对象结构。

## 函数原型

```c
aclError aclrtCreateNotify(aclrtNotify *notify, uint64_t flag);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输出 | Notify 的指针。 |
| flag | 输入 | 使用场景 flag。支持：ACL_NOTIFY_DEFAULT（默认在 Host 上调用）、ACL_NOTIFY_DEVICE_USE_ONLY（仅在 Device 上调用）。宏定义：`ACL_NOTIFY_DEFAULT 0x00000000U`、`ACL_NOTIFY_DEVICE_USE_ONLY 0x00000001U`。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 为空指针 | 提供有效的输出指针 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | 超出硬件 Notify 数量上限等 | 减少创建的 Notify 数量 |

## 约束说明

- 不同型号支持的 Notify 数量不同：950 为 65535，A3/A2 为 8192，Atlas 200I/500 A2 为 2048，Atlas 推理/训练系列为 1024。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L157)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L91)
- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp#L61)
