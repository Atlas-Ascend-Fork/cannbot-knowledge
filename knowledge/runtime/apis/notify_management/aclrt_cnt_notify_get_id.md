---
type: API
title: aclrtCntNotifyGetId
description: 获取 CntNotify 的 ID。仅 950 平台支持。
tags:
- task.lookup
- topic.implementation.resource_query
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
# aclrtCntNotifyGetId

## 功能说明

获取 CntNotify 的 ID。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCntNotifyGetIdImpl`（notify.cpp:200）通过 `rtsCntNotifyGetId(cntNotify, notifyId)` 读取 ID。

## 函数原型

```c
aclError aclrtCntNotifyGetId(aclrtCntNotify cntNotify, uint32_t *notifyId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cntNotify | 输入 | 待获取的 CntNotify。 |
| notifyId | 输出 | CntNotify ID。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 Ascend 950PR/Ascend 950DT 支持。