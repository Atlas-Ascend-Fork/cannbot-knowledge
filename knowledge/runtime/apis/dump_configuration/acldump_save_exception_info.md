---
type: API
title: acldumpSaveExceptionInfo
description: 将自定义异常算子 Tensor 数据保存到异常 Dump 路径下，用于 AI Core Error 分析。
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

# acldumpSaveExceptionInfo

## 功能说明

将自定义异常算子 Tensor 数据保存到异常算子 Dump 路径下。文件路径格式为 `<dumpPath>/extra-info/data-dump/<deviceId>/<fileName>.custom.{timestamp}`。

## 函数原型

```c
aclError acldumpSaveExceptionInfo(const char *fileName, const char *userTag, const acldumpTensorInfo *tensors, size_t tensorCount)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| fileName | 输入 | 目标文件名，相对路径且不能包含 ".." |
| userTag | 输入 | 自定义维测信息，可选 |
| tensors | 输入 | Tensor 数组，addrType 需为 ACL_DUMP_ADDR_RAW，placement 需为 ACL_DUMP_PLACEMENT_DEVICE |
| tensorCount | 输入 | Tensor 数组元素个数 |

## 返回值说明

返回 ACL_SUCCESS 表示成功，其他值表示失败。

## 约束说明

- 需在开启异常算子 Dump 后调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/3_save_exception_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/3_save_exception_info/main.cpp#L123)
