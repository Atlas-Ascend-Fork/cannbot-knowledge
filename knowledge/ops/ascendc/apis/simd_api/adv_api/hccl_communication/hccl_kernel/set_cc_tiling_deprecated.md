---
type: API
title: SetCcTiling（废弃）
description: 用于设置HCCL客户端通信算法的Tiling地址。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/SetCcTiling_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
---

# SetCcTiling（废弃）

> [!NOTE]说明
>该接口废弃，并将在后续版本移除，请不要使用该接口。请使用[SetCcTilingV2](set_cc_tiling_v2.md)接口设置通信算法的Tiling地址。

## 功能说明

用于设置HCCL客户端通信算法的Tiling地址。

## 函数原型

```
__aicore__ inline int32_t SetCcTiling(__gm__ void* ccOpTilingData)
```

## 参数说明

**表1**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| ccOpTilingData | 输入 | 通信算法的[Mc2CcTiling](../hccl_tiling/tiling_data_struct.md#table678914014562)参数的地址。Mc2CcTiling在Host侧计算得出，具体请参考[表2 Mc2CcTiling参数说明](../hccl_tiling/tiling_data_struct.md#table678914014562)，由框架传递到核函数（Kernel）中使用。 |

## 返回值说明

-   HCCL\_SUCCESS，表示成功。
-   HCCL\_FAILED，表示失败。

## 约束说明

-   参数相同的同一种通信算法在调用Prepare接口前只需要调用一次本接口，否则需要多次调用本接口。
-   同一种通信算法只支持设置一个ccOpTilingData地址；对于同一种通信算法，重复调用本接口会覆盖该通信算法的ccOpTilingData地址。
-   若调用本接口，必须与传initTiling地址的[Init](init_deprecated.md)接口配合使用，且Init接口在本接口前被调用。
-   若调用本接口，必须使用标准C++语法定义TilingData结构体的开发方式。


<!-- cannbot:related:start -->
## 相关

- [Init（废弃）](init_deprecated.md)（`related`）：若调用本接口时传入initTiling参数，则必须与SetCcTiling接口配合使用。；若调用本接口，必须与传initTiling地址的Init接口配合使用，且Init接口在本接口前被调用。。Init 与 SetCcTiling 双方正文互相规定配套调用及先后顺序，组成同一 deprecated 初始化合同。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`same_topic`）：用于设置HCCL客户端通信算法的Tiling地址。；用于设置HCCL客户端中某个通信算法配置的TilingData地址。两卡核心对象与决策都是 HCCL 通信算法 Tiling 地址设置，旧接口传 GM 指针且已废弃，V2 改为相对 Mc2InitTiling 的 offset。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子声明的固定版本源码包含对 `SetCcTiling(...)` 的直接调用（第 203 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_all_gather_batch_mat_mul/op_kernel/allto_all_all_gather_batch_mat_mul.h#L203)
- [BatchMatMulReduceScatterAlltoAll A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/batch_mat_mul_reduce_scatter_allto_all.md)（`related`）：算子声明的固定版本源码包含对 `SetCcTiling(...)` 的直接调用（第 272 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/batch_mat_mul_reduce_scatter_allto_all/op_kernel/batch_mat_mul_reduce_scatter_allto_all.h#L272)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
