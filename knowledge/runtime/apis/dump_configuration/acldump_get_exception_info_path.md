---
type: API
title: acldumpGetExceptionInfoPath
description: 获取异常算子 Dump 数据存储路径，用于 AI Core Error 分析。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.error_handling
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/18_dump_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_dump.h
  role: header
source_headers:
- include/external/acl/acl_dump.h
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

# acldumpGetExceptionInfoPath

## 功能说明

获取异常算子 Dump 数据的存储路径。路径格式为 `<dumpPath>/extra-info/data-dump/<deviceId>/`。

需在开启异常算子 Dump 功能后调用。

## 函数原型

```c
aclError acldumpGetExceptionInfoPath(char *path, size_t maxLen)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| path | 输出 | 接收路径的字符数组，建议 4096 字节 |
| maxLen | 输入 | path 内存大小 |

## 返回值说明

返回 ACL_SUCCESS 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/3_save_exception_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/3_save_exception_info/main.cpp#L59)
