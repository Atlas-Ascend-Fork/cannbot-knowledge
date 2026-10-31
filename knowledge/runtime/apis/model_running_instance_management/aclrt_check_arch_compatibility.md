---
type: API
title: aclrtCheckArchCompatibility
description: 根据 AI 处理器版本判断算子指令是否兼容。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.architecture
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/15_model_running_instance_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/model_ri.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310b'
- '310p'
- '910'
---
# aclrtCheckArchCompatibility

## 功能说明

根据 AI 处理器版本判断算子指令是否兼容。

## 函数原型

```c
aclError aclrtCheckArchCompatibility(const char *socVersion, int32_t *canCompatible)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| socVersion | 输入 | AI 处理器版本。 |
| canCompatible | 输出 | 1 表示兼容，0 表示不兼容。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅用于算子指令兼容性判断。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp#L69)
