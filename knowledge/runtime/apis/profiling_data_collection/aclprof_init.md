---
type: API
title: aclprofInit
description: "在 aclInit 之后初始化 Profiling 并设置数据保存路径，须与 Finalize 配对；不能与算子订阅流程交叉调用。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-01_data_profiling_apis.md
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

# aclprofInit

## 功能说明

初始化 Profiling，用于设置保存性能数据文件路径。必须与 [aclprofFinalize](aclprof_finalize.md) 配对使用。

## 函数原型

```c
aclError aclprofInit(const char *profilerResultPath, size_t length)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| profilerResultPath | 输入 | 性能数据文件保存路径，绝对路径或相对路径 |
| length | 输入 | profilerResultPath 长度，最大 4096 字节 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofFinalize](aclprof_finalize.md) 配对使用，建议整个进程只调用一次。
- 需在 [aclInit](../runtime_configuration/acl_init.md) 之后调用。

### 总体约束

不能与订阅算子信息接口交叉调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/0_create_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/0_create_config/main.cpp#L32)
- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L142)
