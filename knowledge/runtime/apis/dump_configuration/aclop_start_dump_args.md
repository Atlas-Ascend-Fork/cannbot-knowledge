---
type: API
title: aclopStartDumpArgs
description: 开启算子信息统计功能，与 aclopStopDumpArgs 配合输出算子信息文件。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
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
- '910'
---

# aclopStartDumpArgs

## 功能说明

开启算子信息统计功能，与 [aclopStopDumpArgs](aclop_stop_dump_args.md) 配合输出算子信息文件。一个 shape 对应一个算子信息文件，包含算子类型、属性、输入输出 format/数据类型/shape 等信息。

## 函数原型

```c
aclError aclopStartDumpArgs(uint32_t dumpType, const char *path)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| dumpType | 输入 | Dump 类型，当前仅支持 ACL_OP_DUMP_OP_AICORE_ARGS (0x00000001U) |
| path | 输入 | 保存路径，绝对路径或相对路径 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅支持单算子 API（aclnn 前缀）执行场景。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/0_adump_args/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/0_adump_args/main.cpp#L47)
