---
type: API
title: GetSortOffset
description: 根据元素位置，获取Sort数据中的对应偏移量（单位为字节）。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.ordering
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# GetSortOffset

## 功能说明

根据元素位置，获取Sort数据中的对应偏移量（单位为字节）。

## 函数原型

```
template <typename T>
__aicore__ inline uint32_t GetSortOffset(const uint32_t elemOffset)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |

**表2**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| elemOffset | 输入 | 元素的位置。 |

## 返回值说明

Sort数据中的对应偏移量。

## 约束说明

无

## 调用示例

```
AscendC::GetSortOffset<half>(128);
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortOffset(...)` 的直接调用（第 430 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/merge_sort_big_size.h#L430)
- [MoeTokenPermute A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute.md)（`related`）：算子声明的固定版本源码包含对 `GetSortOffset(...)` 的直接调用（第 159 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute/op_kernel/moe_mrgsort.h#L159)
- [MoeTokenPermuteWithRoutingMap 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute_with_routing_map_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortOffset(...)` 的直接调用（第 158 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute_with_routing_map/op_kernel/moe_mrgsort.h#L158)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
