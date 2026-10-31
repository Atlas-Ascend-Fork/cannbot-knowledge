---
type: API
title: aclrtCntNotifyDestroy
description: 销毁计数型 Notify（CntNotify）。仅 950 平台支持。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
# aclrtCntNotifyDestroy

## 功能说明

销毁 CntNotify。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCntNotifyDestroyImpl`（notify.cpp:155）通过 `rtCntNotifyDestroy(static_cast<rtCntNotify_t>(cntNotify))` 释放。

## 函数原型

```c
aclError aclrtCntNotifyDestroy(aclrtCntNotify cntNotify);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cntNotify | 输入 | 待销毁的 CntNotify。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 Ascend 950PR/Ascend 950DT 支持。