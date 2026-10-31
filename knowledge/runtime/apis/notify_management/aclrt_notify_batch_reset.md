---
type: API
title: aclrtNotifyBatchReset
description: 批量复位 Notify。昇腾虚拟化实例场景不支持该操作。
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
- a3
- a2
---
# aclrtNotifyBatchReset

## 功能说明

批量复位 Notify。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtNotifyBatchResetImpl`（notify.cpp:83）对 notifies 数组做空校验，通过 `rtsNotifyBatchReset(notifies, static_cast<uint32_t>(num))` 批量复位。num 在内部收窄为 uint32_t。

## 函数原型

```c
aclError aclrtNotifyBatchReset(aclrtNotify *notifies, size_t num);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| notifies | 输入 | Notify 数组。 |
| num | 输入 | Notify 数组的长度。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | notifies 为空指针 | 提供有效的数组 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层批量复位失败 | 检查各 Notify 状态 |

## 约束说明

- 昇腾虚拟化实例场景不支持该操作。