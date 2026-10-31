---
type: API
title: aclrtCntNotifyRecord
description: 在指定 Stream 上记录一个 CntNotify。异步接口，与 aclrtCntNotifyWaitWithTimeout 配合实现多 Stream 同步等待。仅 950 平台支持。
tags:
- task.lookup
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/09_cntNotify_management.md
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
---
# aclrtCntNotifyRecord

## 功能说明

在指定 Stream 上记录一个 CntNotify。异步接口，与 `aclrtCntNotifyWaitWithTimeout` 配合用于多 Stream 同步等待。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCntNotifyRecordImpl`（notify.cpp:166）对 info 做空校验，通过 `rtsCntNotifyRecord(cntNotify, stream, reinterpret_cast<rtCntNotifyRecordInfo_t*>(info))` 下发记录任务。

## 函数原型

```c
aclError aclrtCntNotifyRecord(aclrtCntNotify cntNotify, aclrtStream stream, aclrtCntNotifyRecordInfo *info);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cntNotify | 输入 | 需记录的 CntNotify。 |
| stream | 输入 | 指定 Stream。使用默认 Stream 时传入 NULL。多 Stream 同步场景下（如 Stream2 等 Stream1），此处配置为 Stream1。 |
| info | 输入 | 控制 Record 行为模式，参见 aclrtCntNotifyRecordInfo。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | info 为空指针 | 提供有效的 info 结构 |

## 约束说明

- 仅 Ascend 950PR/Ascend 950DT 支持。