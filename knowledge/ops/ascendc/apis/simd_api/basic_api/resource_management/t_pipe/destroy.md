---
type: API
title: Destroy
description: 释放TPipe资源，用于重复申请释放TPipe，创建TPipe对象后可调用Destroy手动释放资源。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Destroy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_tpipe.h
---

# Destroy<a name="ZH-CN_TOPIC_0000001764926901"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

释放资源。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void Destroy()
```

## 约束说明<a name="section633mcpsimp"></a>

用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

```cpp
AscendC::TPipe pipe; // Pipe内存管理对象
AscendC::TQue<AscendC::TPosition::VECOUT, 2> que; //输出数据Queue队列管理对象，TPosition为VECOUT
uint8_t num = 2;
uint32_t len = 128;
pipe.InitBuffer(que, num, len);
pipe.Destroy();
```


<!-- cannbot:related:start -->
## 相关

- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`related`）：“该接口内部未设置PIPE_ALL同步，需要开发者自行保证同步流水正确。”揭示无全流水同步版本的责任转移；“创建tpipe对象后，可调用Destroy手动释放资源。”给出常规手动释放入口，二者用于按同步保障选择释放方式。
- [Init](init.md)（`related`）：Tpipe对象复用时，要与Destroy接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。；约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。。Init 明确规定复用前先 Destroy，Destroy 则提供手工释放资源的对应动作，两者共同定义 TPipe 重复申请释放的生命周期。
- [TPipe](t_pipe_constructor.md)（`related`）：如果需要使用多个TPipe时，请先调用Destroy接口释放前一个TPipe；创建tpipe对象后，可调用Destroy手动释放资源。构造卡明确同一时刻只能有一个 TPipe，并把再次创建前的释放指向 Destroy；Destroy 卡给出对应资源回收操作，形成直接生命周期合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 22 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AddLora A2 ACLNN 算子知识](../../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 47 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora.cpp#L47)
- [ScatterNd A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/scatter_nd.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_kernel/scatter_nd_update.cpp#L31)
- [BlockSparseAttentionGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 37 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc22/attn_infra/arch/bsag_resource.hpp#L37)
- [ScatterNdUpdate A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/scatter_nd_update.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_kernel/scatter_nd_update.cpp#L31)
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 189 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch22/flash_attention_score_grad_s1s2_bn2gs1s2_basic.h#L189)
- [TopKTopPSample A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/top_k_top_p_sample.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/top_k_top_p_sample_v2/op_kernel/top_k_top_p_sample_v2.cpp#L33)
- [GroupedMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 499 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/grouped_matmul.cpp#L499)
- [TopKTopPSample 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/top_k_top_p_sample_950.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/top_k_top_p_sample_v2/op_kernel/top_k_top_p_sample_v2.cpp#L33)
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 130 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a4w4_pipeline.h#L130)
- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `Destroy(...)` 的直接调用（第 112 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L112)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
