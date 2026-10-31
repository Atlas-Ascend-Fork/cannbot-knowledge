---
type: API
title: aclrtSwitchLabelByIndex
description: 根据标签索引跳转到相应的标签位置，执行该标签所在 Stream 上的任务，同时当前 Stream 上的任务停止执行。异步接口。
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/10_label_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/label.cpp
  role: implementation
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
# aclrtSwitchLabelByIndex

## 功能说明

根据标签索引跳转到相应的标签位置，执行该标签所在 Stream 上的任务，同时当前 Stream 上的任务停止执行。异步接口。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtSwitchLabelByIndexImpl`（label.cpp:85）对 ptr、labelList、stream 均做空校验，通过 `rtsLabelSwitchByIndex(ptr, maxValue, reinterpret_cast<void*>(labelList), static_cast<rtStream_t>(stream))` 下发跳转任务。

## 函数原型

```c
aclError aclrtSwitchLabelByIndex(void *ptr, uint32_t maxValue, aclrtLabelList labelList, aclrtStream stream);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 存放目标标签索引值的 Device 内存地址，数据类型 uint32，索引值从 0 开始。当索引大于 labelList 数组最大索引时，跳转到最大标签。 |
| maxValue | 输入 | 标签列表中的标签个数。 |
| labelList | 输入 | 标签列表。通过 [aclrtCreateLabelList](aclrt_create_label_list.md) 创建。 |
| stream | 输入 | 执行跳转任务的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | ptr、labelList 或 stream 为空指针 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层跳转执行失败 | 检查标签列表与 Stream 状态 |

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L105)
