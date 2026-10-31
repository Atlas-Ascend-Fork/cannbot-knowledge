---
type: API
title: aclsysGetCANNVersion
description: 查询 CANN 软件包版本号（废弃，请使用 aclsysGetVersionNum/Str）。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
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

# aclsysGetCANNVersion

## 功能说明

查询 CANN 软件包版本号。此接口已废弃，请使用 [aclsysGetVersionStr](aclsys_get_version_str.md) 或 [aclsysGetVersionNum](aclsys_get_version_num.md)。

## 函数原型

```c
aclError aclsysGetCANNVersion(aclCANNPackageName name, aclCANNPackageVersion *version)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| name | 输入 | 软件包枚举，参见 aclCANNPackageName |
| version | 输出 | 版本号结构体 |

## 返回值说明

返回 0 表示成功，其他值表示失败。