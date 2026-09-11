---
type: API
title: asc_get_smmu_tag_version
description: 获取SMMU（System Memory Management Unit）版本信息。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_smmu_tag_version.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/utils/sys_var.h
---

# asc_get_smmu_tag_version

## 功能说明

获取SMMU（System Memory Management Unit）版本信息。

## 函数原型

```cpp
__aicore__ inline int64_t asc_get_smmu_tag_version()
```

## 参数说明

无

## 返回值说明

SMMU版本信息。各bit含义如下：
**表1** SMMU标签版本比特位说明

| bit范围    | 含义 |
| ----------- |:----|
| 63:28 | 保留位。 |
| 27:0 | SMMU标签版本。 |
| 27:14 | 年。格式：YY-YYYY-YYYY。 |
| 13:8 | 月。格式：MM-MMMM。 |
| 7:2 | 日。格式：DD-DDDD。 |
| 1:0 | 同一日期的子版本。 |

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
int64_t smmu_tag_version = asc_get_smmu_tag_version();
printf("smmu tag version is %x", smmu_tag_version);// 需用%x将其打印成十六进制的数
```
