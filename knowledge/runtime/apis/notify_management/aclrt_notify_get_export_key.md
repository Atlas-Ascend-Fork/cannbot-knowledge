---
type: API
title: aclrtNotifyGetExportKey
description: 将本进程中的指定 Notify 设置为 IPC Notify 并返回共享名称 key，用于多 Device 不同进程间任务同步。支持进程白名单校验开关。
tags:
- task.lookup
- topic.implementation.cross_process
- topic.implementation.synchronization
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
- a3
- a2
- '310p'
- '910'
---
# aclrtNotifyGetExportKey

## 功能说明

将本进程中的指定 Notify 设置为 IPC Notify，并返回 key（Notify 共享名称），用于多 Device 上不同进程间实现任务同步。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtNotifyGetExportKeyImpl`（notify.cpp:94）对 notify 与 key 均做空校验，通过 `rtsNotifyGetExportKey(notify, key, static_cast<uint32_t>(len), flags)` 导出 key。len 在内部收窄为 uint32_t。

## 函数原型

```c
aclError aclrtNotifyGetExportKey(aclrtNotify notify, char *key, size_t len, uint64_t flags);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 指定 Notify。 |
| key | 输出 | Notify 共享名称。 |
| len | 输入 | 共享名称的长度，最小长度为 65。 |
| flags | 输入 | 是否启用进程白名单校验。ACL_RT_NOTIFY_EXPORT_FLAG_DEFAULT（默认启用校验，需配合 [aclrtNotifySetImportPid](aclrt_notify_set_import_pid.md)）或 ACL_RT_NOTIFY_EXPORT_FLAG_DISABLE_PID_VALIDATION（关闭校验）。宏定义：`ACL_RT_NOTIFY_EXPORT_FLAG_DEFAULT 0x0UL`、`ACL_RT_NOTIFY_EXPORT_FLAG_DISABLE_PID_VALIDATION 0x02UL`。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 或 key 为空指针；len 过小 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层导出失败 | 检查 Notify 状态 |

## 约束说明

- 昇腾虚拟化实例场景不支持该操作。
- 与本接口配合使用的接口流程见 [aclrtNotifyImportByKey](aclrt_notify_import_by_key.md) 的跨进程同步说明。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp#L65)
- [`2_advanced_features/notify/1_ipc_notify_withoutpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/1_ipc_notify_withoutpid/proc_a.cpp#L66)
