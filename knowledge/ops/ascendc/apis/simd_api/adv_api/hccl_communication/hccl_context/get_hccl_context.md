---
type: API
title: GetHcclContext
description: 获取指定Index通信域的context（消息区）地址。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/GetHcclContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
- 310p
---

# GetHcclContext

## 功能说明

获取指定Index通信域的context（消息区）地址。

## 函数原型

```
template <uint32_t index>
__aicore__ inline __gm__ uint8_t* __gm__ GetHcclContext(void)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| index | 模板参数，用来表示要设置的通信域ID，当前只支持2个通信域，index只能为0/1。 |

## 返回值说明

指定通信域的context（消息区）地址。

## 约束说明

当前最多只支持2个通信域。

## 调用示例

```
GM_ADDR contextGM = AscendC::GetHcclContext<0>();
```


<!-- cannbot:related:start -->
## 相关

- [HCCL Context简介](hccl_context_intro.md)（`related`）：“才可以调用GetHcclContext获取对应的context地址。”给出焦点端事实；“获取指定Index通信域的context（消息区）地址。”给出候选端事实。简介卡给出调用 GetHcclContext 前必须完成通信域配置的先决条件，接口卡定义按 Index 取得消息区地址的结果，构成明确的配置后取址链。
- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：获取指定Index通信域的context（消息区）地址。；配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。。HcclGroup 在原型侧声明通信域名称，GetHcclContext 在 Kernel 侧按索引取得该域的 context 地址，二者是通算融合通信域从注册到运行时访问的直接链。
- [SetHcclContext](set_hccl_context.md)（`related`）：设置通算融合算子每个通信域对应的context（消息区）地址。；获取指定Index通信域的context（消息区）地址。。Set 生产按 index 保存的消息区地址，Get 读取同一通信域地址，构成明确的写入/取回合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 25 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AllGatherMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/all_gather_matmul.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 222 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/all_gather_matmul_v2/op_kernel/all_gather_matmul_aiv_mode.h#L222)
- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 200 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_all_gather_batch_mat_mul/op_kernel/allto_all_all_gather_batch_mat_mul.h#L200)
- [AlltoAllMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_matmul.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_matmul/op_kernel/arch22/allto_all_matmul.h#L129)
- [AlltoAllQuantMatmul A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_quant_matmul.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_matmul/op_kernel/arch22/allto_all_matmul.h#L129)
- [AlltoAllvGroupedMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_allv_grouped_mat_mul.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_allv_quant_grouped_mat_mul/op_kernel/mc2_templates/communication/hccl_a2av_op.h#L133)
- [AttentionToFfn A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/attention_to_ffn.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 184 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/attention_to_ffn/op_kernel/attention_to_ffn.h#L184)
- [BatchMatMulReduceScatterAlltoAll A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/batch_mat_mul_reduce_scatter_allto_all.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 269 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/batch_mat_mul_reduce_scatter_allto_all/op_kernel/batch_mat_mul_reduce_scatter_allto_all.h#L269)
- [DistributeBarrier A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/distribute_barrier.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 216 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/distribute_barrier/op_kernel/distribute_barrier.h#L216)
- [FfnToAttention A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/ffn_to_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 99 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/ffn_to_attention/op_kernel/ffn_to_attention.h#L99)
- [GroupedMatMulAllReduce A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/grouped_mat_mul_all_reduce.md)（`related`）：算子声明的固定版本源码包含对 `GetHcclContext(...)` 的直接调用（第 73 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/grouped_mat_mul_all_reduce/op_kernel/arch22/grouped_mat_mul_all_reduce.cpp#L73)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
