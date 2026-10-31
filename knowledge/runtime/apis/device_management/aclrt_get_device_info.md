---
type: API
title: aclrtGetDeviceInfo
description: 获取指定 Device 的指定属性；attr 为 aclrtDevAttr 枚举，内部分两条路径，可映射为 (moduleType, infoType) 的走向 rtGetDeviceInfo，其余走 Misc 分支，未识别的 attr 返回 ACL_ERROR_RT_PARAM_INVALID。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-02_Enumerations.md
  role: supporting
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_device.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-28T06:51:10Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310b'
- '310p'
- '910'
---

# aclrtGetDeviceInfo

## 功能说明

获取指定 Device 的信息。调用方通过 `attr`（`aclrtDevAttr`）选择要查询的属性，结果以 `int64_t` 写入 `value`。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtGetDeviceInfoImpl` 先校验 `value` 非空，再把 `aclrtDevAttr` 原值 `static_cast` 成 `rtDevAttr` 传给 `rtsDeviceGetInfo`；两个枚举的数值一一对应（如 `ACL_DEV_ATTR_CUBE_CORE_NUM` 与 `RT_DEV_ATTR_CUBE_CORE_NUM` 同为 102），本层不做语义转换。
- RTS 层 `ApiImpl::GetDeviceInfoByAttr` 按 `attr` 分派到两条路径：
  - **可直接映射为 (moduleType, infoType)** 的属性走 `GetDeviceInfo(deviceId, moduleType, infoType, val)`，与 `rtGetDeviceInfo` 同一路径：AI CPU / AI Core / Vector Core 数量、`PHY_CHIP_ID`、`SUPER_POD_*` 系列、`CUST_OP_PRIVILEGE`、`MAINBOARD_ID`、`SMP_ID`、`HD_CONNECT_TYPE`、`DEVICE_FORM_FACTOR`。
  - **其余属性**走 `GetDeviceInfoByAttrMisc`：先把调用方的 `deviceId` 经 `Runtime::GetUserDevIdByDeviceId` 转成用户 Device ID（转换失败即返回该错误）；随后 `CUBE_CORE_NUM` 与 `L2_CACHE_SIZE` 从 platform info（`SoCInfo` 的 `cube_core_cnt` / `l2_size`）取值，SIMT 相关属性走 `GetDeviceSimtInfo`，`TOTAL_GLOBAL_MEM_SIZE` 取 `MemGetInfoByDeviceId` 的 totalSize，`NPU_ARCH` 走 `GetDeviceNpuArch`，`IS_VIRTUAL` 走 `GetDeviceVirtualInfo`。
- `GetDeviceInfoByAttrMisc` 未识别的 `attr` 落入 default 分支，报 EE1003 并返回 `RT_ERROR_INVALID_VALUE`。

## 函数原型

```c
aclError aclrtGetDeviceInfo(uint32_t deviceId, aclrtDevAttr attr, int64_t *value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。先用 [aclrtGetDeviceCount](aclrt_get_device_count.md) 取可用数量，取值范围为 `[0, 数量-1]`。 |
| attr | 输入 | 属性类型，类型定义见 `aclrtDevAttr`。 |
| value | 输出 | 属性值的指针，由接口写入。 |

### aclrtDevAttr 属性分类

| 取值段 | 属性 | 说明 |
| --- | --- | --- |
| 1 | ACL_DEV_ATTR_AICPU_CORE_NUM | AI CPU 数量 |
| 101 / 102 | ACL_DEV_ATTR_AICORE_CORE_NUM / ACL_DEV_ATTR_CUBE_CORE_NUM | AI Core / Cube Core 数量 |
| 201–212 | ACL_DEV_ATTR_VECTOR_CORE_NUM、WARP_SIZE、MAX_THREAD_PER_VECTOR_CORE、UBUF_PER_VECTOR_CORE、MAX_GRID_DIM_X/Y/Z、MAX_BLOCK_PER_GRID、MAX_THREADS_PER_BLOCK、MAX_BLOCK_DIM_X/Y/Z | Vector Core 数量与 SIMT 网格/线程块规格；SIMT 类属性仅 Ascend 950 支持，其余型号默认返回 0 |
| 301 / 302 | ACL_DEV_ATTR_TOTAL_GLOBAL_MEM_SIZE / ACL_DEV_ATTR_L2_CACHE_SIZE | Device 全局内存总量 / L2 Cache 大小，单位 Byte |
| 401–410 | ACL_DEV_ATTR_SMP_ID … ACL_DEV_ATTR_SUPER_POD_CHASSIS_ID | 芯片、主板与超节点拓扑标识 |
| 409 | ACL_DEV_ATTR_DEVICE_FORM_FACTOR | 产品形态，返回 `ACL_DEVICE_FORM_FACTOR_POD/A_K/A_X/PCIE_CARD` |
| 501 / 601 | ACL_DEV_ATTR_IS_VIRTUAL / ACL_DEV_ATTR_NPU_ARCH | 是否为算力切分虚拟设备 / NPU 架构 |

`ACL_DEV_ATTR_LOCAL_MEM_PER_VECTOR_CORE`（204）已废弃，与 `ACL_DEV_ATTR_UBUF_PER_VECTOR_CORE` 同值；`ACL_DEV_ATTR_SUPER_POD_DEVIDE_ID`（403）已废弃，与 `ACL_DEV_ATTR_SUPER_POD_DEVICE_ID` 同值。

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `value` 为空指针 |
| `RT_ERROR_INVALID_VALUE` | `ACL_ERROR_RT_PARAM_INVALID`（107000） | `attr` 不在支持范围内（default 分支） |
| 驱动/内部码 | 经 `ErrorcodeManage::GetRtExtErrCode` 映射 | `deviceId` 越界等导致用户 Device ID 反查失败 |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。`ACL_ERROR_INVALID_PARAM` 是 ACL 层错误码，不参与 rtError 映射。

## 约束说明

- `deviceId` 的取值范围是 `[0, 可用 Device 数量)`，与 [aclrtGetDeviceCount](aclrt_get_device_count.md) 的返回一致；超出范围会因用户 Device ID 反查失败而报错。
- SIMT 相关属性（`WARP_SIZE`、`MAX_THREAD_PER_VECTOR_CORE`、`UBUF_PER_VECTOR_CORE` 及 `MAX_*`）仅 Ascend 950 支持，其他产品默认返回 0，不能据返回值 0 判定硬件不具备该能力。
- `attr` 的支持范围依赖具体产品与驱动能力（如超节点 ID、主板 ID），官方接口文档未给出逐属性支持矩阵；上板前应在目标产品核对该属性的返回值。
- 本接口只读取 Device 信息，不改变线程状态；调用前需已能取得 Device ID，通常配合 [aclrtSetDevice](aclrt_set_device.md) 初始化环境。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L67)：查询 `ACL_DEV_ATTR_VECTOR_CORE_NUM`。
- [`6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp#L79)：查询 `ACL_DEV_ATTR_TOTAL_GLOBAL_MEM_SIZE`。
