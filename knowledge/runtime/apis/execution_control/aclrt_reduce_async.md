---
type: API
title: aclrtReduceAsync
description: "在指定 Stream 异步执行 SUM、MIN 或 MAX 归约；源、目标内存与 Stream 须位于同一 Device，支持的数据类型依产品而定。"
tags:
- task.lookup
- topic.compute.reduction
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/12_execution_control.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtReduceAsync

## 功能说明

执行Reduce操作（SUM/MIN/MAX等）。异步接口。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 reserve==nullptr；将 aclDataType 映射为 rtDataType；构造 rtReduceInfo_t 后委托 rtReduce 到 RTS 层。
## 函数原型

```c
aclError aclrtReduceAsync(void *dst, const void *src, uint64_t count, aclrtReduceKind kind, aclDataType type, aclrtStream stream, void *reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针。 |
| src | 输入 | 源内存地址指针。 |
| count | 输入 | 源内存大小（Byte）。 |
| kind | 输入 | 操作类型：aclrtReduceKind。 |
| type | 输入 | 数据类型：aclDataType。 |
| stream | 输入 | 指定执行Reduce操作的Stream。 |
| reserve | 输入 | 预留参数，当前固定传NULL。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

dst、src必须与stream所在的Device是同一个设备。各产品支持的数据类型不同。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/built_in_task/0_reduce_task/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/built_in_task/0_reduce_task/main.cpp#L47)
