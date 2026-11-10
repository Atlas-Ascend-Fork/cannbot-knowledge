---
{
  "type": "Runbook",
  "title": "NPU dropless MoE 路由对基线 capacity-mask topkgating 的精确等价修复",
  "description": "基线 Hunyuan topkgating 的 expert_capacity = max(topk, topk*S//E) 会丢弃超载 (token, expert) 贡献，而 NPU 路由链（npu_moe_gating_top_k_softmax → npu_moe_init_routing_v2 → npu_moe_finalize_routing）是 dropless；S=21 prefill 时 32 层中 24 层 max_load 9–13 > capacity=8，语义差异真实触发（decode S=1 恒不超载）。第一版保护在超载层整层回退 dense per-expert 路径，融合收益丢失（prefill 仅 1174 ms）。修复为：超载时用 topkgating 重建精确 router_probs × dispatch_mask 权重并 gather 回 topk 序、把被丢弃贡献置零，路由仍走 grouped-matmul；修复后 prefill 193 ms、golden cosine 0.99989（修复前 0.99966）、贪心 token 全匹配，掩码分支被 reviewer 独立确认真实触发。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# NPU dropless MoE 路由对基线 capacity-mask topkgating 的精确等价修复

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（HunYuanMoEV1ForCausalLM）在 torch_npu 上把 dense MoE（einsum dispatch + 64 专家逐块计算）替换为 `npu_moe_gating_top_k_softmax` → `npu_moe_init_routing_v2` → FP8 `npu_grouped_matmul`（+`npu_swiglu`）→ `npu_moe_finalize_routing` 路由链。
- 平台/版本：Ascend950PR_9589 单卡，torch_npu 2.12.0，CANN 9.1.0，W8A8 FP8 静态 per-tensor。
- 目标：在保留基线 `topkgating` 的 expert-capacity 丢弃语义（drop token）前提下获得融合收益——用户约束「保精度优先：dropless 不得引入精度漂移」。
- 缺失信息：容量结论仅在该 21-token 负载与 tiny 模型上验证；其他负载分布未逐层枚举。

## 触发与观测

- 故障/风险触发：基线 `topkgating` 的 `expert_capacity = max(topk, topk*tokens//num_experts)`（S=21、topk=8、E=64 时 = 8）会丢弃超载 (token, expert) 贡献；NPU 路由链是 dropless（finalize_routing 按 scales 加权聚合全部 topk 贡献）。S=21 prefill 实测 32 层中 24 层 max_load 9–13 > capacity=8——语义差异真实、高频触发；decode（S=1）恒不超载。
- 修复前观测（第一版保护：超载层整层回退 dense per-expert 路径）：`HY_MOE_DEBUG=1` 日志显示大量层 `fused=FALLBACK`，prefill 仅 1174.00 ms（融合收益在超载层全部丢失）；该版本 golden 对齐 cosine 0.99966、top10 重叠 8/10。

## 探针与操作

修复（超载时重建精确上游权重、路由保持 grouped-matmul；`HunYuanMoE._fused_forward` 逐字）：

```
        # Capacity semantics: upstream ``topkgating`` drops tokens beyond
        # max(topk, topk*S//E) per expert. Fused routing is dropless, so when any
        # expert would overflow we rebuild the *exact* upstream assignment
        # weights (router_probs * capacity_dispatch_mask) and mask the dropped
        # (token, expert) contributions to zero. The routing itself stays
        # grouped-matmul; only the combiner weight is corrected, so dropping is
        # bit-equivalent to the baseline while keeping the fused expert compute.
        if S > 1:
            counts = torch.bincount(topk_idx.flatten(), minlength=E)
            capacity = max(K, K * S // E)
            max_load = int(counts.max().item())
            if max_load > capacity:
                _, combine_weights, _, _ = topkgating(logits, K)
                w_eff = combine_weights.sum(dim=-1).type_as(topk_weight)  # [S, E]
                topk_weight = torch.gather(w_eff, 1, topk_idx.long())
            if os.environ.get("HY_MOE_DEBUG", "0") == "1" and not getattr(self, "_dbg_logged", False):
                self._dbg_logged = True
                print(f"[moe] layer{self.layer_idx} S={S} max_load={max_load} "
                      f"capacity={capacity} overload={'yes(masked)' if max_load > capacity else 'no'}",
                      flush=True)
```

修复前行为日志（逐字，来源记录#339）：

```
[moe] layer16 S=21 max_load=9 capacity=8 fused=FALLBACK
[moe] layer17 S=21 max_load=8 capacity=8 fused=yes
[moe] layer18 S=21 max_load=9 capacity=8 fused=FALLBACK
[moe] layer19 S=21 max_load=10 capacity=8 fused=FALLBACK
```

修复后行为日志（逐字，来源记录#165）：

```
[moe] layer0 S=21 max_load=9 capacity=8 overload=yes(masked)
[moe] layer9 S=21 max_load=13 capacity=8 overload=yes(masked)
[moe] layer13 S=21 max_load=8 capacity=8 overload=no
```

## 机制与判别

- 丢弃语义只影响 combine 权重：基线 `combine_weights = einsum(router_probs, dispatch_mask)` 中超载 (token, expert) 的分量为 0；因此用基线 `topkgating` 重建 `w_eff = combine_weights.sum(-1)` 再 gather 回 topk 序，被丢弃贡献在 `topk_weight` 中即为 0，`npu_moe_finalize_routing` 的加权聚合结果与基线丢弃语义等价，同时专家计算仍走 grouped-matmul（被丢弃行的结果乘 0 权重，不改变聚合）。
- 与回退方案的可区分点：dense 回退在超载层完全放弃融合（性能退回 dense 量级）；精确掩码只在 host 侧多一次轻量 `topkgating` 权重重建，保留 GMM 计算。
- decode（S=1）capacity = max(8, 0) = 8 且单 token 仅激活 8 个专家各 1 行，恒不超载，掩码分支不触发——与 reviewer 独立观测一致。
- 未验证推断：掩码重建在极长序列/大 batch 下的 `topkgating` 重算开销未单独计时（单层一次性、预期占比小）；被丢弃行仍参与 GMM 计算属已知冗余（相对 dense 仍大幅减少）。

## 验证信号

（平台：Ascend950PR_9589 单卡 / torch_npu 2.12.0 / CANN 9.1.0；同负载 batch 1、21-token prefill、8-token 输出，warm-up 后单次观测）

- c1：基线 topkgating 的 expert_capacity = max(topk, topk*S//E) 会丢弃超载 (token, expert) 贡献，而 NPU 路由链为 dropless；S=21 prefill 时 32 层中 24 层 max_load 9–13 > capacity=8，语义差异真实触发；decode（S=1）恒不超载。〔signals：来源记录#165（reviewer 复测 24/32 层 masked）、来源记录#339（implementer 首测 FALLBACK）〕
- c2：超载层从『整层回退 dense per-expert 路径』改为『重建精确 router_probs × dispatch_mask 权重置零被丢弃贡献、路由保持 grouped-matmul』后，同负载 Prefill 由 1174.00 ms 降至 193.13 ms（单次观测）。〔signals：来源记录#339（修复前 1174.00 ms）→ #351（修复后 193.13 ms）〕
- c3：修复后端到端精度与基线语义对齐：prefill cosine 0.99989（修复前 dense-fallback 版本 0.99966）、top10 重叠 9/10（修复前 8/10）、贪心 token 全匹配且无首个分歧步。〔signals：来源记录#347；reviewer 独立复核 来源记录#120 cosine 0.99989 / token_match=true〕
- 旁证：tiny 随机模型 fused vs dense 路径 max_abs=0.0（来源记录#248）；修复后全融合 prefill 176.33–193 ms 区间、`bash infer.sh` 复测 187.74 ms（来源记录#404），均与 193.13 ms 同量级（单次观测）。

## 适用与失效边界

- 适用：任何「基线带 capacity/drop 语义、目标实现为 dropless NPU 路由」的 MoE 迁移，且丢弃语义可表达为对 combine 权重的置零。
- 边界/条件：掩码重建假设基线丢弃逻辑只作用于组合权重（`router_probs × dispatch_mask`），若基线在专家输入侧也过滤（不计算被丢行），本方案多算被丢行但不改结果（权重为 0）；每层每次前向需一次 `torch.bincount` 同步读 max_load（S>1 时），超敏感时延场景需评估。
- 失效/回退：若 capacity 语义含随机丢弃或与 topk 顺序相关的复杂规则（如按 token_priority 排序的容量分配），须直接复用基线 `topkgating` 重建（本方案即如此实现）；若负载恒不超载（如 decode S=1 或 S 足够大使 capacity ≥ 实际负载），掩码分支不触发、纯 dropless 即等价。
- 停止条件：掩码修复后 golden 对齐（cosine/token match）或 packed 多 batch 一致性失败时，回退整层 dense 路径（`HY_ENABLE_MOE_FUSION=0` 可组级回退）。
