---
type: API
title: HCCL集合通信Wait
description: 阻塞AI Core，非细粒度通信时，等待handleId对应的通信任务完成，细粒度通信时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# Wait

## 功能说明

阻塞AI Core，非[细粒度通信](iterate.md)时，等待handleId对应的通信任务完成，[细粒度通信](iterate.md)时，等待handleId对应的[步长](../hccl_tiling/set_step_size.md)长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过[GetBlockIdx](../../../basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)指定其在某一个核上运行。

## 函数原型

```
__aicore__ inline int32_t Wait(HcclHandle handleId)
```

## 参数说明

**表1**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| handleId | 输入 | 对应通信任务的标识ID，只能使用Prepare原语接口的返回值。<br>using HcclHandle = int8_t; |

## 返回值说明

-   0，表示成功
-   -1，表示失败

## 约束说明

-   调用本接口前确保已调用过[InitV2](init_v2.md)和[SetCcTilingV2](set_cc_tiling_v2.md)接口。
-   入参handleId只能使用Prepare原语对应接口的返回值。
-   本接口在AIC核或者AIV核上调用必须与对应的Prepare接口的调用核保持一致。
-   非[细粒度通信](iterate.md)时，本接口的调用次数应该与Prepare的repeat次数一致，[细粒度通信](iterate.md)时，本接口的调用次数应该与通信任务的总步骤数/步长\*Prepare的repeat次数一致。handleId调用Wait接口的顺序，必须和Prepare接口一致。

## 调用示例

```
REGISTER_TILING_DEFAULT(ReduceScatterCustomTilingData); // ReduceScatterCustomTilingData为对应算子头文件定义的结构体
GET_TILING_DATA_WITH_STRUCT(ReduceScatterCustomTilingData, tilingData, tilingGM);
Hccl hccl;
GM_ADDR contextGM = AscendC::GetHcclContext<0>(); // AscendC自定义算子kernel中，通过此方式获取HCCL context
__gm__ void* mc2InitTiling = (__gm__ void*)(&tiling->mc2InitTiling);
__gm__ void* mc2CcTiling = (__gm__ void*)(&(tiling->mc2CcTiling));
hccl.InitV2(contextGM, &tilingData);
auto ret = hccl.SetCcTilingV2(offsetof(ReduceScatterCustomTilingData, mc2CcTiling));
if (ret != HCCL_SUCCESS) {
    return;
}
if (AscendC::g_coreType == AIC) {
    HcclHandle handleId =
        hccl.ReduceScatter(sendBuf, recvBuf, 100, HcclDataType::HCCL_DATA_TYPE_INT8, HcclReduceOp::HCCL_REDUCE_SUM, 10);

    for (uint8_t i = 0; i < 10; i++) {
        hccl.Commit(handleId); // 通知服务端可以执行上述的ReduceScatter任务
    }
    for (uint8_t i = 0; i < 10; i++) {
        hccl.Wait(handleId); // 阻塞接口，需等待上述ReduceScatter任务执行完毕
    }
    hccl.Finalize(); // 后续无其他通信任务，通知服务端执行上述ReduceScatter任务之后即可退出
}
```


<!-- cannbot:related:start -->
## 相关

- [AllGather](all_gather.md)（`related`）：返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。；阻塞AI Core，非［细粒度通信］(iterate.md)时，等待handleId对应的通信任务完成，［细粒度通信］(iterate.md)时，等待handleId对应的步长长度的子通信任务完成。。AllGather 产出的有效 handleId 被 Wait 用于等待相同通信任务完成，联合阅读可闭合下发到完成同步。
- [Iterate](iterate.md)（`related`）：阻塞AI Core，非［细粒度通信］(iterate.md)时，等待handleId对应的通信任务完成，［细粒度通信］(iterate.md)时，等待handleId对应的步长长度的子通信任务完成。；sync（输入）：bool类型。是否需要等待当前通信步骤完成再进行后续计算或通信任务，参数取值如下：true：默认值，表示阻塞并等待当前通信步骤完成。该参数取值为true时，无需再调用Wait接口等待通信任务完成。两接口通过 Iterate 的 sync 选择共同决定每个细粒度步骤是否另行 Wait。
- [Query（HCCL集合通信）](query.md)（`related`）：Query 用于“查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。”；Wait 用于“等待handleId对应的通信任务完成”。二者分别支持非阻塞进度观测和阻塞完成，是同一 handle 生命周期的两种同步策略。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 15 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 345 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_all_gather_batch_mat_mul/op_kernel/allto_all_all_gather_batch_mat_mul.h#L345)
- [AlltoAllMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_matmul.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 146 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/mc2_templates/communication/communicator/hccl_communicator.h#L146)
- [AlltoAllQuantMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_quant_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 146 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/mc2_templates/communication/communicator/hccl_communicator.h#L146)
- [BatchMatMulReduceScatterAlltoAll A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/batch_mat_mul_reduce_scatter_allto_all.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 584 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/batch_mat_mul_reduce_scatter_allto_all/op_kernel/batch_mat_mul_reduce_scatter_allto_all.h#L584)
- [InplaceMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L124)
- [InplaceQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L124)
- [InplaceWeightQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_weight_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L124)
- [MatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L124)
- [MatmulAlltoAll A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_allto_all.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 146 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/mc2_templates/communication/communicator/hccl_communicator.h#L146)
- [MatmulAlltoAll 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_allto_all_950.md)（`related`）：算子声明的固定版本源码包含对 `Wait(...)` 的直接调用（第 146 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/mc2_templates/communication/communicator/hccl_communicator.h#L146)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
