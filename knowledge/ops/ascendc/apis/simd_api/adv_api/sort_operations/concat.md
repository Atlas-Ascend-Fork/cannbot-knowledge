---
type: API
title: Concat（排序操作）
description: 对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.ordering
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Concat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# Concat

## 功能说明

对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行[Sort](sort.md)。

## 函数原型

```
template <typename T>
__aicore__ inline void Concat(LocalTensor<T>& concat, const LocalTensor<T>& src, const LocalTensor<T>& tmp, const int32_t repeatTime)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| concat | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>LocalTensor的起始地址需要32字节对齐。 |
| src | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>LocalTensor的起始地址需要32字节对齐。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| tmp | 输入 | 临时空间。接口内部复杂计算时用于存储中间变量，由开发者提供，临时空间大小的获取方式请参考[GetConcatTmpSize](get_concat_tmp_size.md)。数据类型与源操作数保持一致。<br><br>类型为[LocalTensor](../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>LocalTensor的起始地址需要32字节对齐。 |
| repeatTime | 输入 | 重复迭代次数，int32_t类型，每次迭代处理16个元素，下次迭代跳至相邻的下一组16个元素。取值范围：repeatTime∈[0,255]。 |

## 返回值说明

无

## 约束说明

-   操作数地址对齐要求请参见[通用地址对齐约束](../../general_description_and_constraints.md#section796754519912)。

## 调用示例

请参见[MrgSort](mrg_sort.md)的[调用示例](mrg_sort.md#section642mcpsimp)。


<!-- cannbot:related:start -->
## 相关

- [GetConcatTmpSize](get_concat_tmp_size.md)（`related`）：获取Concat接口所需的临时空间大小。；对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。。GetConcatTmpSize 给 Concat 排序预处理接口计算所需临时空间，形成 Host 资源准备到 kernel 预处理的直接合同。
- [Sort](sort.md)（`related`）：焦点卡说明“预处理完成后可进行Sort操作”，候选卡则要求 Sort“配合Concat（预处理）和Extract（结果提取）使用”；Concat 是排序前的实际数据整形阶段，而不是仅同属排序目录的 sibling。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 283 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/merge_sort_big_size.h#L283)
- [MoeDistributeDispatchSetup 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_setup_950.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 853 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_setup/op_kernel/arch35/moe_distribute_dispatch_setup_arch35.h#L853)
- [MoeDistributeDispatchTeardown 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_teardown_950.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 853 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_setup/op_kernel/arch35/moe_distribute_dispatch_setup_arch35.h#L853)
- [MoeInitRoutingV3 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_init_routing.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 110 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_init_routing_v3/op_kernel/moe_v3_full_load.h#L110)
- [MoeInitRoutingV3 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_init_routing_950.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 265 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_init_routing_v3/op_kernel/arch35/moe_v3_full_load_base.h#L265)
- [MoeTokenPermute A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 94 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute/op_kernel/moe_sort_one_core.h#L94)
- [MoeTokenPermuteWithRoutingMap 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/moe/moe_token_permute_with_routing_map_950.md)（`related`）：算子声明的固定版本源码包含对 `Concat(...)` 的直接调用（第 94 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute_with_routing_map/op_kernel/moe_sort_one_core.h#L94)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
