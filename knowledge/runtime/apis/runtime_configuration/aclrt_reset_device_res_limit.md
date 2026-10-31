---
type: API
title: aclrtResetDeviceResLimit
description: 重置当前进程的 Device 资源限制，恢复默认配置。重置后可通过 aclrtGetDeviceResLimit 查询默认值。
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
# aclrtResetDeviceResLimit

## 功能说明

调用 `aclrtSetDeviceResLimit` 设置 Device 资源限制后，可调用本接口重置当前进程的 Device 资源限制，恢复默认配置，此时可通过 `aclrtGetDeviceResLimit` 查询默认的资源限制。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtResetDeviceResLimitImpl`（device.cpp:426）通过 `rtsResetDeviceResLimit(deviceId)` 恢复设备级资源限制为默认值。

## 函数原型

```c
aclError aclrtResetDeviceResLimit(int32_t deviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID，取值范围 [0, 可用 Device 数 - 1]。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L123)
