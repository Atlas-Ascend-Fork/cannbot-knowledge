---
type: Runbook
title: 混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单
description: 混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单。在昇腾上部署含线性注意力分支的混合注意力模型（Gated-DeltaNet / Mamba 类 chunk 递推）时，出现精度不达标——gsm8k 等评测明显低于预期、图模式比单算子模式差、输出错乱但无显式报错。线性注意力的 chunk 递推 / 状态 cache / gating 与融合算子交织，有几处易被忽视的精度点，按下面逐条对号入座、作为首查项。
tags:
- task.debugging
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/321
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/270
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/402
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# 混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单

## 适用场景

在昇腾上部署含线性注意力分支的混合注意力模型（[Gated-DeltaNet](../../concepts/modules/gated_deltanet.md) / Mamba 类 chunk 递推）时，出现精度不达标——gsm8k 等评测明显低于预期、图模式比单算子模式差、输出错乱但**无显式报错**。线性注意力的 chunk 递推 / 状态 cache / gating 与融合算子交织，有几处易被忽视的精度点，按下面逐条对号入座、作为首查项。

## 陷阱 1：融合算子版本过旧（先钉 CANN 版本再排查逻辑）

Prefill 整段 chunk 计算走 `torch_npu.npu_chunk_gated_delta_rule` 融合算子（一次完成 chunk 内 L2 归一化、decay、下三角求解、递推状态更新）时，该算子为**近期合入**，早于 CANN 9.1.0 的包上有精度正确性隐患。**动作**：发现 GDN Prefill 精度异常（或部署前做基线）时，先确认/钉定 CANN 9.1.0+ 再排查建模逻辑，把「CANN 版本过旧」列为该算子精度回归的首查根因。Decode 阶段的 [npu_recurrent_gated_delta_rule](../../concepts/kernels/recurrent_gated_delta_rule.md) 未同样标注版本要求。

## 陷阱 2：图模式对 padding 请求的元数据填充值

线性注意力后端在图捕获（CUDA graph 路径）时用 padding 请求补齐固定 batch；padding 位的 Mamba 状态索引 / seq_len 填充值属图元数据。上游默认填 `-1`（状态索引）/ `1`（seq_len fill）在昇腾图路径下会让 padding 位读到错误状态、污染真实请求输出，表现为**同权重同输入下图模式 accuracy 明显低于单算子模式**。修法：两处均改填 `0`。

```python
mamba_indices[bs - num_padding :] = 0        # 原默认 -1
def get_cuda_graph_seq_len_fill_value(self):
    if is_npu():
        return 0                              # 原默认 1
    return 1
```

## 陷阱 3：状态 cache 索引循环回 0（调大 cache 容量降触发频率）

维护者确认的已知框架问题：Mamba 内部索引 `mamba_cache_indices == 0` 时会产生错误结果；该索引在 Mamba cache 容量范围内**循环使用**，`max-mamba-cache-size` 默认值偏小（通常为 2）→ 频繁回到 0 → 频繁触发精度下降。失败信号是推理精度异常/输出错误而无报错。**缓解**：把 `max-mamba-cache-size` 调大（推荐 512，平衡精度与性能），显著降低触发概率，代价是一定 cache 容量开销——这是降触发频率、非根治。

## 陷阱 4：激活内化进融合算子后，回退分支须自补该激活

一旦把某激活（此处 GDN gating 的 beta `sigmoid`）下沉进融合算子内部，产出该值的 gating 函数就改成返回 **raw**（未激活）值——此后所有**不走**该融合算子的回退/旁路分支必须自行补回该激活，否则精度错误：

```python
# gating 上游从 return g, b.sigmoid().unsqueeze(0)  改为  return g, b   （返回 raw beta）
# 走融合算子分支：传 raw beta，sigmoid 由算子内部做
# 未使能融合的回退分支：必须显式补
beta = beta.sigmoid().unsqueeze(0)
```

可迁移原则：把某激活内化进融合算子，等于给它加了一条隐式 correctness 合约——新增任何非融合 code path（MTP verify、硬件不满足回退等）都要检查是否需自补该激活。

## 参考实现及其约束

- 参考实现：cann-recipes-infer 的 [Qwen3-Next](../../concepts/models/qwen3_next.md)（[SGLang](../../concepts/frameworks/sglang.md) + Atlas A3，含 Mamba/GDN 分支）与 [Qwen3.5-MoE](../../concepts/models/qwen3_5_moe.md) 的 linear attention 层。
- 陷阱 2/4 的补丁打在 SGLang 上游文件（`hybrid_linear_attn_backend.py` / `ascend_backend.py`）；陷阱 3 是 SGLang 服务侧配置项。陷阱 1 系于 `npu_chunk_gated_delta_rule` 这一算子的版本演进。
- 边界：结论限定到证据覆盖的 Qwen3-Next / Qwen3.5（Mamba/GDN 混合线性注意力），不外推到其它后端或模型；512 / CANN 9.1.0 是经验推荐值。线性注意力吃序列并行（打破 chunk 递推跨 rank 顺序依赖）另见 [qwen3-next-gdn-context-parallel-zeco](../../guides/experience/interventions/qwen3_next_gdn_context_parallel_zeco.md)。

## Evidence

- diff 事实 + 仓自报（@45627e9e）：`MambaAttnBackendBase` 两处填充值改 0；图模式 gsm8k 0.70→0.96（仓自报、无独立复测）。溯源下探 [cann-recipes-infer-pr-321-fix-sglang-graph-mode-precision](https://gitcode.com/cann/cann-recipes-infer/merge_requests/321)
- 维护者确认 + doc 披露（@be33ff59ad77）：`mamba_cache_indices=0` 症状+根因+512 缓解由维护者答复 + README「注意事项」第 8 条给出；无精度/性能量化数字。溯源下探 [cann-recipes-infer-pr-270-feat-qwen3-next-rmsnormgated-gdr](https://gitcode.com/cann/cann-recipes-infer/merge_requests/270)
- diff 事实（@be33ff59ad77）：`fused_gdn_gating.py` 尾行 `return g, b.sigmoid()` → `return g, b`，融合/回退两分支 beta 处理差异。溯源同上 pr-270。
- doc 披露（@843c3dd61a35）：Qwen3.5-MoE 优化文档 ChunkGDR 小节的 CANN 9.1.0 版本钉定建议（维护者随代码合入、预防性钉定、无独立精度复测 artifact）。溯源下探 [cann-recipes-infer-pr-402-feat-support-qwen3-5](https://gitcode.com/cann/cann-recipes-infer/merge_requests/402)

<!-- cannbot:related:start -->
## 相关

- [Gated DeltaNet (GDN)](../../concepts/modules/gated_deltanet.md)（`related`）：Prefill 整段 chunk 计算走 `torch_npu.npu_chunk_gated_delta_rule` 融合算子（一次完成 chunk 内 L2 归一化、decay、下三角求解、递推状态更新）时，该算子为**近期合入**，早于 CANN 9.1.0 的包上有精度正确性隐患。**动作**：发现 GDN Prefill 精度异常（或部署前做基线）时，先确认/钉定 CANN 9.1.0+ 再排查建模逻辑，把「CANN 版本过旧」列为该算子精度回归的首查根因。Decode 阶段的 ［npu_recurrent_gated_delta_rule］(../../concepts/kernels/recurrent_gated_delta_rule.md) 未同样标注版本要求。；- **Prefill kernel 选择**：Qwen3-Next 走 PyPTO ChunkGDN；Qwen3.5-MoE 走 torch_npu 原生 `torch_npu.npu_chunk_gated_delta_rule`（另有 PyTorch `solve_triangular` 回退路径）。运行手册的版本首查项直接补充概念页所列 Qwen3.5-MoE Prefill 原生算子的精度边界。
- [recurrent_gated_delta_rule](../../concepts/kernels/recurrent_gated_delta_rule.md)（`related`）：一旦把某激活（此处 GDN gating 的 beta `sigmoid`）下沉进融合算子内部，产出该值的 gating 函数就改成返回 **raw**（未激活）值——此后所有**不走**该融合算子的回退/旁路分支必须自行补回该激活，否则精度错误：；Decode/MTP 阶段 ［gated-deltanet］(../modules/gated_deltanet.md) 的融合算子，用于混合注意力模型（［qwen3-next］(../models/qwen3_next.md)、［qwen3-5-moe］(../models/qwen3_5_moe.md)）线性注意力层的单步/少量 draft token 递推。一次 kernel launch 完成 Sigmoid + L2Norm + Gated Delta 递推注意力 + `ssm_state` 选择性更新，消除 Decode GDN 路径多个小算子的 Launch 和中间搬运开销。BF16 输入输出、FP32 累加，AIV 单元执行（`KERNEL_TYPE_AIV_ONLY`）。运行手册的旁路补激活规则由该融合算子内部执行 Sigmoid 的合同直接解释。
<!-- cannbot:related:end -->
