---
type: API
title: aclrtSetDeviceResLimit
description: 设置当前进程的 Device 资源限制。应在 aclrtSetDevice 之后、执行算子之前使用。多次设置以最后一次为准。
tags:
- task.lookup
- topic.implementation
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/03_runtime_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
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
# aclrtSetDeviceResLimit

## 功能说明

设置当前进程的 Device 资源限制。应在 `aclrtSetDevice` 之后且在执行算子之前调用。多次设置以最后一次为准。

资源限制优先级：Stream 级别 > 进程级别 > AI 处理器硬件默认。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtSetDeviceResLimitImpl`（device.cpp:413）通过 `rtsSetDeviceResLimit(deviceId, static_cast<rtDevResLimitType_t>(type), value)` 写入。

## 函数原型

```c
aclError aclrtSetDeviceResLimit(int32_t deviceId, aclrtDevResLimitType type, uint32_t value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID，取值范围 [0, 可用 Device 数 - 1]。 |
| type | 输入 | 资源类型，参见 aclrtDevResLimitType。 |
| value | 输入 | 资源限制的大小。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 设置仅对后续下发的任务有效。
- 在捕获 Stream 任务到模型中再执行的场景下（如 [aclmdlRICaptureBegin](../model_running_instance_management/aclmdl_ri_capture_begin.md)/End），需在捕获之前设置。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L142)
- [`2_advanced_features/kernel/1_launch_kernel_with_reslimit/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/1_launch_kernel_with_reslimit/main.cpp#L68)
