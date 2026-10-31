---
type: API
title: aclrtProfTrace
description: 在网络指定位置下发自定义 Profiling 打点（异步）。
tags:
- task.lookup
- topic.performance.analysis
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtProfTrace

## 功能说明

支持在网络指定位置下发自定义 Profiling 打点。异步接口，向指定 Stream 下发打点任务。length 建议 18 字节，超出校验报错。

内部行为（固定 commit 源码结论）：实现中调用 `rtsProfTrace(userdata, length, stream)`。

## 函数原型

```c
aclError aclrtProfTrace(void *userdata, int32_t length, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| userdata | 输入 | 自定义信息 |
| length | 输入 | userdata 长度，建议 18 字节 |
| stream | 输入 | 指定 Stream |

## 返回值说明

返回 0 表示成功，其他值表示失败。