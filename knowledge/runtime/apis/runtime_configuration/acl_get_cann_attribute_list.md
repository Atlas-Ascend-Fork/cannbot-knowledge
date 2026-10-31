---
type: API
title: aclGetCannAttributeList
description: 查询运行环境中 CANN 软件和 AI 处理器支持的特性列表。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_base_rt.h
  role: header
source_headers:
- include/external/acl/acl_base_rt.h
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

# aclGetCannAttributeList

## 功能说明

查询运行环境中 CANN 软件和对应 AI 处理器支持的特性枚举列表。无需用户提前申请内存，进程退出时自动释放。

## 函数原型

```c
aclError aclGetCannAttributeList(const aclCannAttr **cannAttrList, size_t *num)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| cannAttrList | 输出 | 特性枚举数组 |
| num | 输出 | 支持的特性数量 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp#L50)
