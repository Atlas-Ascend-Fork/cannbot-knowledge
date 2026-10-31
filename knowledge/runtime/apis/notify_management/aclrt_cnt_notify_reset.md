---
type: API
title: aclrtCntNotifyReset
description: 复位一个 CntNotify，将计数值清空为 0。异步接口。仅 950 平台支持。
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
# aclrtCntNotifyReset

## 功能说明

复位一个 CntNotify，将 CntNotify 的计数值清空为 0。异步接口。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCntNotifyResetImpl`（notify.cpp:189）通过 `rtsCntNotifyReset(cntNotify, stream)` 下发复位任务。

## 函数原型

```c
aclError aclrtCntNotifyReset(aclrtCntNotify cntNotify, aclrtStream stream);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cntNotify | 输入 | 待复位的 CntNotify。 |
| stream | 输入 | 指定 Stream。使用默认 Stream 时传入 NULL。多 Stream 同步场景下（如 Stream2 等 Stream1），此处配置为 Stream2。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 Ascend 950PR/Ascend 950DT 支持。