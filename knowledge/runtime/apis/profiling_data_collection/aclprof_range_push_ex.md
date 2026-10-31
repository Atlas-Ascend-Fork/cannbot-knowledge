---
type: API
title: aclprofRangePushEx
description: "在 Torch 算子加载前缓存待上报的 Tensor 信息，之后由 RangePop 上报；与 msproftx 时间区间标记区分。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-02_msproftx_extension_apis.md
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

# aclprofRangePushEx

## 功能说明

在 Torch 场景下，用户在算子加载前调用此接口，后调用 [aclprofRangePop](aclprof_range_pop.md) 完成 Profiling 数据上报。内部判断 messageType 为 MESSAGE_TYPE_TENSOR_INFO 时缓存 Tensor 信息。

## 函数原型

```c
aclError aclprofRangePushEx(aclprofEventAttributes *attr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| attr | 输入 | 待上报的 Tensor 信息，参见 aclprofEventAttributes |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofRangePop](aclprof_range_pop.md) 配对使用。