---
type: API
title: aclrtCreateStream
description: "C++ Stream 创建封装，接收 priority 和 flag，转调 aclrtCreateStreamWithConfig；用于选择优先级和流模式。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
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

# aclrtCreateStream

## 功能说明

在当前进程或线程中创建Stream。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtCreateStreamWithConfig。

## 函数原型

```cpp
aclError aclrtCreateStream(aclrtStream *stream, uint32_t priority, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输出 | Stream的指针。类型定义请参见aclrtStream。 |
| priority | 输入 | 优先级。<br>该参数取值范围：[0, 7]，总共最多支持8个优先级，数字越小代表优先级越高，其中，0的优先级最高，7的优先级最低。如果设置的优先级超过取值范围，则就近修正为边界值。 |
| flag | 输入 | Stream指针的flag。<br>flag参数值请参见C接口aclrtCreateStreamWithConfig中的“flag取值说明”。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
