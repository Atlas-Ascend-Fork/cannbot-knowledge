---
type: API
title: aclrtNotifyImportByKey
description: 在本进程中获取 key 的信息，返回本进程可使用的 Notify 指针。支持开启两 Device 间数据交互。
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
# aclrtNotifyImportByKey

## 功能说明

在本进程中获取 key 的信息，并返回本进程可以使用的 Notify 指针。与 `aclrtNotifyGetExportKey` 等接口配合实现多 Device 不同进程间的任务同步。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtNotifyImportByKeyImpl`（notify.cpp:107）对 notify 与 key 均做空校验，通过 `rtsNotifyImportByKey(notify, key, flags)` 导入共享 Notify。

## 函数原型

```c
aclError aclrtNotifyImportByKey(aclrtNotify *notify, const char *key, uint64_t flags);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输出 | Notify 指针。 |
| key | 输入 | Notify 共享名称。必须先调用 [aclrtNotifyGetExportKey](aclrt_notify_get_export_key.md) 获取后再作为入参传入。 |
| flags | 输入 | 是否开启两个 Device 之间的数据交互。ACL_RT_NOTIFY_IMPORT_FLAG_DEFAULT（默认关闭，需调用 aclrtDeviceEnablePeerAccess 开启）或 ACL_RT_NOTIFY_IMPORT_FLAG_ENABLE_PEER_ACCESS（直接开启）。宏定义：`ACL_RT_NOTIFY_IMPORT_FLAG_DEFAULT 0x0UL`、`ACL_RT_NOTIFY_IMPORT_FLAG_ENABLE_PEER_ACCESS 0x02UL`。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 或 key 为空指针 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | 导入失败（IPC Notify 已释放等） | 确保导入前 IPC Notify 未释放 |

## 约束说明

- 昇腾虚拟化实例场景不支持该操作。
- 调用前需确保 IPC Notify 未提前释放。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp#L73)
- [`2_advanced_features/notify/1_ipc_notify_withoutpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/1_ipc_notify_withoutpid/proc_b.cpp#L82)
