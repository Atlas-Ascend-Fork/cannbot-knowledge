---
type: API
title: aclrtCreateLabel
description: 创建标签。每个进程最多创建 65535 个标签。配合 aclrtCreateLabelList、aclrtSetLabel、aclrtSwitchLabelByIndex 实现 Stream 间跳转。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
# aclrtCreateLabel

## 功能说明

创建标签。每个进程最多创建 65535 个标签。创建后需配合 `aclrtCreateLabelList`、`aclrtSetLabel`、`aclrtSwitchLabelByIndex` 实现 Stream 之间的跳转。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtCreateLabelImpl`（label.cpp:22）对 label 指针做空校验，通过 `rtsLabelCreate(static_cast<rtLabel_t*>(label))` 创建底层标签。

## 函数原型

```c
aclError aclrtCreateLabel(aclrtLabel *label);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| label | 输出 | 标签的指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | label 为空指针 | 提供有效的输出指针 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | 超出进程最大标签数等 | 减少标签数量 |

## 约束说明

- 每个进程最多创建 65535 个标签。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L95)
