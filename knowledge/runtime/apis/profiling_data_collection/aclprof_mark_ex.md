---
type: API
title: aclprofMarkEx
description: "向指定 Stream 下发带字符串的打点任务，关联 Host 与 Device 打点；消息最长 127 字符。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-02_msproftx_extension_apis.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
source_headers:
- include/external/acl/acl_prof.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofMarkEx

## 功能说明

aclprofMarkEx 打点接口。向指定 Stream 下发打点任务，用于关联 Host 侧与 Device 侧打点任务。

## 函数原型

```c
aclError aclprofMarkEx(const char *msg, size_t msgLen, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| msg | 输入 | 打点信息字符串 |
| msgLen | 输入 | 字符串长度，最大 127 字符 |
| stream | 输入 | 指定的 Stream |

## 返回值说明

返回 0 表示成功，其他值表示失败。