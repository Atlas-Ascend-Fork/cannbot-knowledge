---
type: API
title: aclrtNotifySetImportPid
description: 设置共享 Notify 的进程白名单。与 aclrtNotifyGetExportKey 配合，实现多 Device 不同进程间的任务同步。
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
# aclrtNotifySetImportPid

## 功能说明

设置共享 Notify 的进程白名单，与 `aclrtNotifyGetExportKey`（启用白名单校验时）配合使用。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtNotifySetImportPidImpl`（notify.cpp:120）对 notify 与 pid 数组均做空校验，通过 `rtsNotifySetImportPid(notify, pid, static_cast<int32_t>(num))` 设置白名单。num 在内部收窄为 int32_t。

## 函数原型

```c
aclError aclrtNotifySetImportPid(aclrtNotify notify, int32_t *pid, size_t num);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 指定 Notify，与 [aclrtNotifyGetExportKey](aclrt_notify_get_export_key.md) 中的 Notify 保持一致。 |
| pid | 输入 | 白名单进程 ID 数组。可通过 aclrtDeviceGetBareTgid 获取（Docker 场景下为物理机进程 ID）。 |
| num | 输入 | 白名单进程数量，与 pid 数组大小一致。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 或 pid 为空指针 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层设置失败 | 检查白名单进程 ID 合法性 |

## 约束说明

- 昇腾虚拟化实例场景不支持该操作。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp#L76)
