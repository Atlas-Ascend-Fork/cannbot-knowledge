---
type: Runbook
title: FIA 的 MLA 无量化路径硬约束 group_num ∈ {2 的幂}（否则 561002 / CheckFeatureMlaNoQuantShape 失败）
description: '若该调用发生在 图捕获期（init_device_graphs → graph capture，取 FIA workspace 时），最外层抛 Capture ... graph failed: ... aclnnFusedInferAttentionScoreV3 failed, error code is 561002，进程直接拉不起。'
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/125
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a2
---

# FIA 的 MLA 无量化路径硬约束 group_num ∈ {2 的幂}（否则 561002 / CheckFeatureMlaNoQuantShape 失败）

## 信号（现象）

在昇腾上跑 [MLA](../../concepts/modules/mla.md) 结构模型（query/key head_dim=512），调 [FIA](../../concepts/kernels/fused_infer_attention_score.md) 算子 `aclnnFusedInferAttentionScoreV3` 失败，error code **561002**，算子自陈的诊断直接列出支持集与观测值：

```
call aclnnFusedInferAttentionScoreV3 failed, error code is 561002
EZ9999: In NO_QUANT situation, rope exsists and query/key head dim = 512,
        group num should be in 1, 2, 4, 8, 16, 32, 64, 128, but got 5
        [FUNC:CheckFeatureMlaNoQuantShape][FILE:fused_infer_attention_score_tiling_check_feature.cpp]
        FusedInferAttentionScore do tiling failed, ret is -1.
```

若该调用发生在 [图捕获](../../concepts/techniques/npu_graph_mode.md)期（`init_device_graphs` → graph capture，取 FIA workspace 时），最外层抛 `Capture ... graph failed: ... aclnnFusedInferAttentionScoreV3 failed, error code is 561002`，**进程直接拉不起**。

## 触发条件

FIA 的 **MLA 无量化路径**——`NO_QUANT` + 带 rope + query/key head_dim=512——且实际传入的 **group_num**（每个 KV 组的 query-head 数 / GQA 比）**不是 2 的幂**（本例传入 5）。观测于 SGLang NPU backend（[SGLang](../../concepts/frameworks/sglang.md)）走 MTP 路径取 FIA workspace 时。

## 根因

约束来自 **FIA 算子自身的 tiling 特性检查** `CheckFeatureMlaNoQuantShape`：MLA 无量化路径（带 rope、q/k head_dim=512）硬性要求 group_num 为 2 的幂且落在 `{1, 2, 4, 8, 16, 32, 64, 128}`。这是 **CANN FIA 算子对 MLA 无量化 shape 的支持约束**，不是模型自身或建模层的能力问题；归因在框架-算子层。约束由算子运行时诊断**自陈**（非报告者臆测），符号 / FILE / 支持集 / 观测值 `got 5` 均在一手 trace 里。

## 修法

- **使 FIA 无量化 MLA 路径实际拿到的 group_num 落在 `{1, 2, 4, 8, 16, 32, 64, 128}`**（算子错误信息直接列明的支持集）。遇到 561002 / `CheckFeatureMlaNoQuantShape` 时，先按这条硬约束核对 group_num，而非怀疑建模代码。
- 具体怎样让 group_num 成为 2 的幂——调整 [TP](../../concepts/parallelism/tensor_parallel.md) / head 切分、kv-group 配置，或改走支持该 group_num 的算子分支 / 量化路径——**未经维护者确认，属推断**，须实测。

## 适用边界

严格限「CANN FIA 算子 `NO_QUANT` + rope + head_dim=512 的 MLA 路径」这一条约束，不外推为整栈通用律，也不代表 FIA 对量化路径 / 其它 head_dim 有同样限制。为什么本例 group_num=5（是否 num_q_heads/num_kv_heads 比、或 MTP/TP 切分所致）为推断。FIA 的另一条**跨后端**调用约束（`actual_seq_lengths_kv` 类型随后端不同）见 [fia-actual-seq-lengths-kv-backend-type](../runtime/fia_actual_seq_lengths_kv_backend_type.md)；融合算子按硬件 / shape 条件门控的更一般情形见 [fused-op-hardware-conditional-fallback](../../optimizations/experience/rules/fused_op_hardware_conditional_fallback.md)。

## 相关经验
- [FIA/qlens 的 block_table 首维 / num_reqs / TND se](../runtime/fia_qlens_block_table_num_reqs_batch_contract.md)
- [MLA 开图模式硬约束 num_heads/num_kv_heads ∈ {32,64,12](../compilation/mla_graph_mode_queries_per_kv_head_ratio_set.md)

## Evidence

- **运行时 artifact（算子自陈）**：事件页完整复现算子诊断——error code 561002 + `CheckFeatureMlaNoQuantShape` + FILE/LINE + 支持集 `{1,2,4,8,16,32,64,128}` 与观测值 `got 5`，是 CANN 算子 tiling 检查的运行时输出，约束由算子自陈。**维护者确认**归因层（属 SGLang 框架 + FA 算子层、指向 SGLang 社区 / ops-transformers 跟进），未额外确认 / 否认约束本身。FIA 算子源码（`fused_infer_attention_score_tiling_check_feature.cpp` 在 CANN / ops-transformers、非本仓）未独立 clone，约束以算子自身诊断为一手依据；「为何 group_num=5」与具体修法旋钮均标为推断。
  - 溯源下探：[cann-recipes-infer-issue-125-bug-report-glm4-7-flash-910b3-call-aclnnfusedinferattentionscorev3-faile](https://gitcode.com/cann/cann-recipes-infer/issues/125)

<!-- cannbot:related:start -->
## 相关

- [MLA (Multi-head Latent Attention)](../../concepts/modules/mla.md)（`related`）：在昇腾上跑 ［MLA］(../../concepts/modules/mla.md) 结构模型（query/key head_dim=512），调 ［FIA］(../../concepts/kernels/fused_infer_attention_score.md) 算子 `aclnnFusedInferAttentionScoreV3` 失败，error code **561002**，算子自陈的诊断直接列出支持集与观测值：；DeepSeek-V3 系列（DeepSeek-R1、Kimi-K2）使用的低秩压缩注意力机制。前者定位 MLA 结构在 FIA tiling 的 group_num 失败，后者解释低秩 KV、NoPE/RoPE 通道与 head 维度来源，可用于核对触发形态。
- [MLA 开图模式硬约束 num_heads/num_kv_heads ∈ {32,64,128}（每 rank 比值出集合则图编译期 EZ9999 / CheckMlaAttrs 失败）](mla_graph_mode_queries_per_kv_head_ratio_set.md)（`related`）：FIA 图模式约束为“图模式下 FIA 的 tiling 校验 `CheckMlaAttrs`（`incre_flash_attention_tiling_check.cc`）只接受 `numHeads/numKvHeads ∈ {32, 64, 128}`。”，FIA MLA 无量化路径则限定另一条“group_num 为 2 的幂且落在 `{1, 2, 4, 8, 16, 32, 64, 128}`”的 CheckFeatureMlaNoQuantShape 合同；对照两类约束可按错误码和支持集避免把两种 FIA/MLA 编译失败混诊。
- [npu_fused_infer_attention_score (v1 / v2)](../../concepts/kernels/fused_infer_attention_score.md)（`related`）：在昇腾上跑 ［MLA］(../../concepts/modules/mla.md) 结构模型（query/key head_dim=512），调 ［FIA］(../../concepts/kernels/fused_infer_attention_score.md) 算子 `aclnnFusedInferAttentionScoreV3` 失败，error code **561002**，算子自陈的诊断直接列出支持集与观测值：；昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算：`softmax(QKᵀ/√d)·V`，支持 Paged KVCache、Block-Table、分离的 NoPE/RoPE Query/Key 输入、以及 Query / Key / Value 三端的动态 Int8 反量化（dequant_scale_*）。失败卡给出 FIA V3 的 tiling 约束，概念卡补齐 FIA 的输入布局与量化入口，能从报错回到实际算子合同。
<!-- cannbot:related:end -->
