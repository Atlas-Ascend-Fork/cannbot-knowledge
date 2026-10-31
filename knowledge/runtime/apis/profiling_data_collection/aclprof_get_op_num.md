---
type: API
title: aclprofGetOpNum
description: 获取指定内存中算子的数量。
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-03_subscription_to_operator_information.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
source_headers:
- include/external/acl/acl_prof.h
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

# aclprofGetOpNum

## 功能说明

获取指定内存中算子的数量。

## 函数原型

```c
aclError aclprofGetOpNum(const void *opInfo, size_t opInfoLen, uint32_t *opNumber)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| opInfo | 输入 | 算子信息内存地址，按 [aclprofGetOpDescSize](aclprof_get_op_desc_size.md) 的整数倍申请 |
| opInfoLen | 输入 | 算子信息长度 |
| opNumber | 输出 | 算子数量 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/2_subscribe_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/2_subscribe_model/main.cpp#L28)
