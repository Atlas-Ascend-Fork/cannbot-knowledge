---
type: API
title: aclrtCacheLastTaskExtendInfo
description: 捕获模式下缓存自定义扩展信息到最后下发的任务上。
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310p'
---

# aclrtCacheLastTaskExtendInfo

## 功能说明

将自定义扩展信息（JSON 格式 UTF-8 编码）缓存到最后下发的任务上。可通过 [aclmdlRIDebugJsonPrint](../model_running_instance_management/aclmdl_ri_debug_json_print.md) 导出 JSON，用 tracing 方式查看。

## 函数原型

```c
aclError aclrtCacheLastTaskExtendInfo(const char* const extendInfoPtr, const size_t infoSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| extendInfoPtr | 输入 | JSON 格式自定义信息地址（Host 内存，UTF-8 编码） |
| infoSize | 输入 | 内存大小，(0, 4K]，超过 4K 仅缓存前 4K |

## 返回值说明

返回 0 表示成功，其他值表示失败。