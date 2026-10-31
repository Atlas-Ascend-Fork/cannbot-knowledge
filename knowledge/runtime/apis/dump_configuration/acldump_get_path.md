---
type: API
title: acldumpGetPath
description: 获取 Dump 数据存储路径，方便用户将自定义维测数据保存到同一目录。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.resource_query
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
- a3
- a2
---

# acldumpGetPath

## 功能说明

获取 Dump 数据的存储路径。需在 [aclmdlInitDump](aclmdl_init_dump.md)/[aclmdlSetDump](aclmdl_set_dump.md) 或通过 [aclInit](../runtime_configuration/acl_init.md) 配置 Dump 信息后调用。

## 函数原型

```c
const char* acldumpGetPath(acldumpType dumpType)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| dumpType | 输入 | Dump 类型，请参见 acldumpType |

## 返回值说明

返回 Dump 路径字符串。返回 NULL 表示未查询到路径。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/0_adump_args/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/0_adump_args/main.cpp#L23)
- [`5_performance/adump/1_adump_callback/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/1_adump_callback/main.cpp#L34)
- [`5_performance/adump/2_model_dump_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/2_model_dump_config/main.cpp#L30)
