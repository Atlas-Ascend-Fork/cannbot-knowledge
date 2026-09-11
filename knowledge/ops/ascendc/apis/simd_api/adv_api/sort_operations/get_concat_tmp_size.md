---
type: API
title: GetConcatTmpSize
description: 获取Concat接口所需的临时空间大小，单位为字节。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.ordering
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetConcatTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/sort/sort_tiling_intf.h
---

# GetConcatTmpSize

## 功能说明

获取Concat接口所需的临时空间大小，单位为字节。

## 函数原型

```
uint32_t GetConcatTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t elemCount, const uint32_t dataTypeSize)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| ascendcPlatform | 输入 | 传入硬件平台的信息，PlatformAscendC定义请参见[构造及析构函数](../../../utils_api/platform_info/platform_ascend_c/constructor_and_destructor.md)。 |
| elemCount | 输入 | 输入元素个数。 |
| dataTypeSize | 输入 | 输入数据大小（单位为字节）。 |

## 返回值说明

Concat接口所需的临时空间大小的字节数。

## 约束说明

无

## 调用示例

```
fe::PlatFormInfos platform_info;
auto plat = platform_ascendc::PlatformAscendC(&platform_info);
const uint32_t elemCount = 128;
AscendC::GetConcatTmpSize(plat, elemCount, 2);
```


<!-- cannbot:related:start -->
## 相关

- [Concat（排序操作）](concat.md)（`related`）：获取Concat接口所需的临时空间大小。；对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。。GetConcatTmpSize 给 Concat 排序预处理接口计算所需临时空间，形成 Host 资源准备到 kernel 预处理的直接合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `GetConcatTmpSize(...)` 的直接调用（第 1250 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_host/arch35/sort_tiling_arch35.cpp#L1250)
- [TopK 950 Direct Invoke 算子知识](../../../../operators/direct/math/math/top_k_950.md)（`related`）：算子声明的固定版本源码包含对 `GetConcatTmpSize(...)` 的直接调用（第 479 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/top_k_v2/op_host/arch35/top_k_v2_tiling_arch35.cpp#L479)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
