---
type: API
title: acldumpRegCallback
description: 注册 Dump 数据回调函数，支持通过回调直接获取 Dump 数据而非落盘。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.callback
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

# acldumpRegCallback

## 功能说明

注册 Dump 数据回调函数。注册后 Dump 数据通过回调函数分发给用户，不再落盘。

配合 [aclmdlInitDump](aclmdl_init_dump.md)/[aclmdlFinalizeDump](aclmdl_finalize_dump.md) 使用。

## 函数原型

```c
aclError acldumpRegCallback(int32_t (* const messageCallback)(const acldumpChunk *, int32_t), int32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| messageCallback | 输入 | 回调函数指针，接收 acldumpChunk 格式的 Dump 数据 |
| flag | 输入 | 回调后是否还落盘，当前仅支持 0（不落盘） |

### acldumpChunk 结构

```c
typedef struct acldumpChunk {
    char       fileName[ACL_DUMP_MAX_FILE_PATH_LENGTH];
    uint32_t   bufLen;
    uint32_t   isLastChunk;
    int64_t    offset;
    int32_t    flag;
    uint8_t    dataBuf[0];
} acldumpChunk;
```

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 注册回调后 Dump 数据不再落盘，两者互斥。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/1_adump_callback/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/1_adump_callback/main.cpp#L105)
