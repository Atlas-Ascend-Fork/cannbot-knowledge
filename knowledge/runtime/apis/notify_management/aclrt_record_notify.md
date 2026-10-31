---
type: API
title: aclrtRecordNotify
description: 在指定 Stream 上记录一个 Notify。异步接口，与 aclrtWaitAndResetNotify 配合实现多 Stream 同步。
tags:
- task.lookup
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtRecordNotify

## 功能说明

在指定 Stream 上记录一个 Notify。异步接口，与 `aclrtWaitAndResetNotify` 配合用于多 Stream 同步等待。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtRecordNotifyImpl`（notify.cpp:49）对 notify 做空校验，通过 `rtsNotifyRecord(static_cast<rtNotify_t>(notify), static_cast<rtStream_t>(stream))` 在目标 Stream 上记录。

## 函数原型

```c
aclError aclrtRecordNotify(aclrtNotify notify, aclrtStream stream);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notify | 输入 | 待记录的 Notify。 |
| stream | 输入 | 指定 Stream。多 Stream 同步场景下（如 Stream2 等 Stream1），此处配置为 Stream1。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notify 为空指针 | 提供有效的 Notify |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层记录失败 | 检查 Stream/Notify 状态 |

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L169)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L161)
- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp#L86)
