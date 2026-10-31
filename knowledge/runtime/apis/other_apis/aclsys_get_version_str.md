---
type: API
title: aclsysGetVersionStr
description: 根据软件包名称查询字符串类型版本号。
tags:
- task.lookup
- topic.implementation.resource_query
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

# aclsysGetVersionStr

## 功能说明

根据软件包名称查询版本号（字符串类型），与 version.info 中的 version 字段保持一致。

## 函数原型

```c
aclError aclsysGetVersionStr(char *pkgName, char *versionStr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| pkgName | 输入 | 软件包名称 |
| versionStr | 输出 | 版本号字符串，建议长度为 ACL_PKG_VERSION_MAX_SIZE（128） |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L25)
- [`0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp#L39)
