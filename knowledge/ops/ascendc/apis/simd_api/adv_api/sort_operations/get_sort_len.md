---
type: API
title: GetSortLen
description: 根据元素数量，获取Sort数据的大小（单位为字节）。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.ordering
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# GetSortLen

## 功能说明

根据元素数量，获取Sort数据的大小（单位为字节）。

## 函数原型

```
template <typename T>
__aicore__ inline uint32_t GetSortLen(const uint32_t elemCount)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |

**表2**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| elemCount | 输入 | 输入元素个数。 |

## 返回值说明

sort数据的大小（单位为字节）。

## 约束说明

无

## 调用示例

```
AscendC::GetSortLen<half>(128);
```


<!-- cannbot:related:start -->
## 相关

- [Sort](sort.md)（`related`）：获取Sort接口处理的数据长度。；排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。。GetSortLen 按 repeatTime 计算 Sort 处理长度，Sort 卡给出该长度所服务的降序 score/index 执行接口与临时空间合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 167 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/sort_merge_intra_core.h#L167)
- [MoeDistributeDispatchSetup 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_setup_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 851 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_setup/op_kernel/arch35/moe_distribute_dispatch_setup_arch35.h#L851)
- [MoeDistributeDispatchTeardown 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_teardown_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 851 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_setup/op_kernel/arch35/moe_distribute_dispatch_setup_arch35.h#L851)
- [MoeInitRoutingV3 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_init_routing.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 109 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_init_routing_v3/op_kernel/moe_v3_full_load.h#L109)
- [MoeInitRoutingV3 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_init_routing_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 264 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_init_routing_v3/op_kernel/arch35/moe_v3_full_load_base.h#L264)
- [MoeTokenPermute A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 118 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute/op_kernel/moe_mrgsort.h#L118)
- [MoeTokenPermuteWithRoutingMap 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute_with_routing_map_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortLen(...)` 的直接调用（第 117 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute_with_routing_map/op_kernel/moe_mrgsort.h#L117)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
