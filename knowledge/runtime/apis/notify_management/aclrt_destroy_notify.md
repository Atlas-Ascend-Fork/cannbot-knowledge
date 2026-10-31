---
type: API
title: aclrtDestroyNotify
description: 销毁 Notify。IPC Notify 需所有涉及进程都销毁后才真正释放。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.cross_process
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
# aclrtDestroyNotify

## 功能说明

销毁 Notify。对于 IPC Notify，所有涉及该 Notify 的进程都完成释放操作后，Notify 才真正释放。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtDestroyNotifyImpl`（notify.cpp:37）对 notify 做空校验，通过 `rtsNotifyDestroy(static_cast<rtNotify_t>(notify))` 释放。

## 函数原型

```c
aclError aclrtDestroyNotify(aclrtNotify notify);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 待销毁的 Notify。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 为空指针 | 提供有效的 Notify |
| `ACL_GET_ERRCODE_RTS(rtErr)` | 销毁时资源占用冲突等 | 确保任务已完成再销毁 |

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L180)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L224)
- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp#L94)
