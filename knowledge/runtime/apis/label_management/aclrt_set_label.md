---
type: API
title: aclrtSetLabel
description: 在 Stream 上设置标签。Stream 需预先通过 aclmdlRIBindStream 绑定过模型运行实例。
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
# aclrtSetLabel

## 功能说明

在 Stream 上设置标签。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtSetLabelImpl`（label.cpp:34）对 label 与 stream 均做空校验，通过 `rtsLabelSet(static_cast<rtLabel_t>(label), static_cast<rtStream_t>(stream))` 将标签设置到指定 Stream。

## 函数原型

```c
aclError aclrtSetLabel(aclrtLabel label, aclrtStream stream);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| label | 输入 | 标签。通过 [aclrtCreateLabel](aclrt_create_label.md) 创建。 |
| stream | 输入 | 需设置标签的 Stream。仅支持通过 [aclmdlRIBindStream](../model_running_instance_management/aclmdl_ri_bind_stream.md) 接口绑定过模型运行实例的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | label 或 stream 为空指针 | 提供有效参数 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | Stream 不符合约束条件（未绑定模型运行实例） | 先绑定 Stream |

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L109)
