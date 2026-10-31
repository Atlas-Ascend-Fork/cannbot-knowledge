---
type: API
title: aclrtCntNotifyCreate
description: "创建利用计数值实现任务间同步的 CntNotify，计数范围为 1 至 UINT32_MAX；普通 Notify 仅支持计数值 1，仅 Ascend 950PR/950DT 支持 CntNotify。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
---
# aclrtCntNotifyCreate

## 功能说明

创建 CntNotify。CntNotify 利用计数值实现任务间同步：与 Notify 的区别是，Notify 的计数值仅支持 1，CntNotify 的计数值支持 [1, uint32_t 最大值]。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCntNotifyCreateImpl`（notify.cpp:144）未对 cntNotify 做空指针校验，通过 `rtCntNotifyCreateServer(static_cast<rtCntNotify_t*>(cntNotify), flag)` 创建。

## 函数原型

```c
aclError aclrtCntNotifyCreate(aclrtCntNotify *cntNotify, uint64_t flag);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| cntNotify | 输出 | CntNotify 的指针。 |
| flag | 输入 | 预留参数，当前固定配置为 0。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 Ascend 950PR/Ascend 950DT 支持。