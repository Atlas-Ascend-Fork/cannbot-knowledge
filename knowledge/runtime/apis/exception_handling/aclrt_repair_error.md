---
type: API
title: aclrtRepairError
description: 基于 aclrtGetErrorVerbose 获取的详细信息进行故障恢复。应在提交任务中止之后调用。试验特性。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/13_exception_handling.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-31T02:15:45Z'
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtRepairError

## 功能说明

基于 [aclrtGetErrorVerbose](aclrt_get_error_verbose.md) 获取的详细信息进行故障恢复。应在提交任务中止之后调用。试验特性。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 完成 aclrt 到 RTS 类型的反向转换后委托 `rtsRepairError(rtsDeviceId, &rtsErrorInfo)` 到 RTS 层。

## 函数原型

```c
aclError aclrtRepairError(int32_t deviceId, const aclrtErrorInfo *errorInfo)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。 |
| errorInfo | 输入 | 错误信息结构体。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
