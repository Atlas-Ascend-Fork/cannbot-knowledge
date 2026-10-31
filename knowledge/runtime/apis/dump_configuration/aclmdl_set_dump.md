---
type: API
title: aclmdlSetDump
description: 设置 Dump 参数（JSON 配置文件路径），控制模型/单算子/异常/溢出 Dump 行为。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/18_dump_configuration.md
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

# aclmdlSetDump

## 功能说明

设置 Dump 参数，通过 dumpCfgPath 指定 JSON 配置文件路径。同一个进程内可多次调用，配置覆盖策略使得后调用生效。

仅在调用后加载的模型受该配置影响。

### 配置类型

- **模型 Dump 配置**：导出模型每层算子输入输出，与指定模型比对定位精度。默认不启用。
- **单算子 Dump 配置**：导出单个算子输入输出，与指定算子比对定位精度。默认不启用。
- **异常算子 Dump 配置**：导出异常算子数据，用于 AI Core Error 分析。
- **溢出算子 Dump 配置**：导出溢出算子数据，用于溢出原因分析。
- **算子 Dump Watch 模式**：开启指定算子输出观察模式，排查内存踩踏。
- **算子 Kernel 调测信息 Dump**：导出 Ascend C 算子 Kernel 调测信息。

## 函数原型

```c
aclError aclmdlSetDump(const char *dumpCfgPath)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| dumpCfgPath | 输入 | 配置文件路径（JSON 格式），包含文件名。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅在调用后加载的模型受 Dump 配置影响。
- 多次调用对同一模型采用覆盖策略。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/2_model_dump_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/2_model_dump_config/main.cpp#L28)
