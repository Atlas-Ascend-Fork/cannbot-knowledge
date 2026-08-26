---
type: Concept
title: Ring Attention Sequence Parallelism
description: Ring Attention 是另一种长序列 SP 方案：与 Ulysses 不同，**attention 内部也保持序列切分**，每张卡仅维护自己那 1/SP 的 Q；通过 概念上以 P2P 环形逐跳传 KV，但本仓 module/unified_sp/core.py 实际用一次 all_gather_into_tensor 把其他 rank 的 1/SP KV 一次性收齐，对本地 FA 与远端合并 FA 两路输出做 LSE（Log-Sum-Exp）合并（非逐跳 P2P）。适合 Ulysses 规模受限（`num_heads` 不够切）或与 Ulysses 组成 2D hybrid SP 的场景。 Wan2.2-I2V 在此基础上实现了 ring-attention-overlap：异步 AllGather + 本地 FA 并行，用计算掩盖通信。
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Ring Attention Sequence Parallelism

## Summary

Ring Attention 是另一种长序列 SP 方案：与 Ulysses 不同，**attention 内部也保持序列切分**，每张卡仅维护自己那 1/SP 的 Q。概念上（见下方 HunyuanVideo 文档引用）以 P2P 环形逐跳传递 KV；但本仓 `module/unified_sp/core.py` 的实际实现是用一次 `all_gather_into_tensor` 把其他所有 rank 的 1/SP KV 一次性收齐，再对「本地 FA」与「其他 rank 合并 FA」共 2 路输出做 LSE（Log-Sum-Exp）合并（非逐跳 P2P、非 SP-1 串行轮）。适合 Ulysses 规模受限（`num_heads` 不够切）或与 Ulysses 组成 2D hybrid SP 的场景。

Wan2.2-I2V 在此基础上实现了 [ring-attention-overlap](../techniques/ring_attention_overlap.md)：异步 AllGather + 本地 FA 并行，用计算掩盖通信。

## Mechanism

![Ring Attention](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/figures/ring.png)
*来源：[`docs/models/hunyuan-video/figures/ring.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/figures/ring.png)（cann-recipes-infer @ 2f82d10；原图来源 [feifeibear/long-context-attention](https://github.com/feifeibear/long-context-attention)）*

> 源（HunyuanVideo 优化文档）：首先将 input 沿着 S 维度切分为 S/SP，其中 SP 为序列并行数量，输入模型。当 attn 计算时，保持本卡的 1/SP 的 Q 不动，通过 P2P(Peer-To-Peer)，将当前维护的 1/SP 的 KV 对传递给下一张卡。每张卡循环接收其他卡的 KV 对，与本卡的 Q 计算注意力。

```mermaid
flowchart LR
 In["Input [B, S, N, D]"] --> Split["S 切分 → 每卡维护 [B, S/SP, N, D]"]
 Split --> Local["本地 FA：本卡 Q × 本卡 KV → out_local, lse_local"]
 Split --> Gather["all_gather_into_tensor 一次收齐<br/>其他 rank 的 1/SP KV"]
 Gather --> Others["其他 rank FA：本卡 Q × 合并 KV → out_others, lse_others"]
 Local --> Merge["_merge_two_outputs：2 路 LSE 合并"]
 Others --> Merge
 Merge --> Out["[B, S/SP, N, D]"]
```

### 两条执行路径

`core.py` 的 `UnifiedSPAttention` 由 `SPConfig.use_ring_overlap`（默认 `True`）切换两条 Ring 路径，均在 `_forward_core` 中按 `if self.use_ring_overlap` 选择：

- `_ring_attention_overlap`（默认）：以 `async_op=True` 异步发起 KV 的 `all_gather_into_tensor`，在通信进行时先算本地 FA（`out_local, lse_local`），`handle.wait()` 后再算其他 rank 的合并 FA（`out_others, lse_others`），用计算掩盖通信，详见 [ring-attention-overlap](../techniques/ring_attention_overlap.md)。
- `_ring_attention_allgather`：串行先 `all_gather_into_tensor` 收齐全部 KV，拼成整段 KV 后做单次 `_compute_attention`，无重叠。

### LSE 两路合并

两条路径的多 rank 输出由 `_merge_two_outputs(out1, lse1, out2, lse2)` 做数值稳定的 2 路合并：先取 `max_lse = max(lse1, lse2)` 重标定，`lse_new = max_lse + log(exp(lse1-max_lse) + exp(lse2-max_lse))`，再以 `weight_i = exp(lse_i - lse_new)` 加权求和 `out_merged = weight1*out1 + weight2*out2`。注意该函数仅合并两路（本地 vs 其他 rank 合并），并非逐轮累积。

## Applicable Scenarios

- `num_heads` 太小、无法满足 Ulysses `num_heads % SP == 0` 的限制（即使启用 UAA 也会超填充预算）
- 与 Ulysses 组合 hybrid SP（外层 Ulysses × 内层 Ring，扩大可用总并行度）
- 显存带宽充裕、P2P 延迟可接受的拓扑

## Configuration

- `ring_group` / `ulysses_group` 由各模型的分布式管理层构造后传入：Wan2.2-I2V 在 `wan/distributed/parallel_mgr.py`（`ulysses_group=PROCESS_GROUP.ULYSSES_PG, ring_group=PROCESS_GROUP.RING_PG`），HunyuanVideo 在 `hyvideo/inference.py`（`get_sp_group().ulysses_group / .ring_group`）。`module/unified_sp/core.py` 的 `UnifiedSPAttention.__init__` 只消费这两个进程组（`self.ulysses_pg = ulysses_group; self.ring_pg = ring_group`），不构造它们
- 可与 `ulysses_anything` / FP8 量化解耦使用（但 FP8 量化 attention 当前不支持 Ring，仅支持 Ulysses）

## Constraints

- 本仓实现以一次 `all_gather_into_tensor` 收齐 ring 组内其他 rank 的 KV（而非逐跳 P2P 的 SP-1 串行轮），通信量随 ring 组大小增长
- Attention 输出需要 2 路（本地 / 其他 rank）LSE 合并，对实现精度更敏感
- 不兼容 FP8 量化 attention（HunyuanVideo 文档明示）
- 与 [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md) 的协同未在钉定版（@2f82d10）代码中验证：`sample_video.py` 的 sparse 分支仅在 `sparse_method != "no_sparse"` 时替换 block.forward，未见 `ring_degree > 1` 的互斥守卫，故不在此断言两者强制互斥
- Ring 将计算与通信串行化时掩盖率低，需要借助 overlap 技巧（见 [ring-attention-overlap](../techniques/ring_attention_overlap.md)）

## Known Deployments

- **Wan2.2-I2V**：多卡 Ring Attention + AllGather overlap，详见 `module/unified_sp/core.py`
- **HunyuanVideo**：作为与 Ulysses 并列的 SP 选项纳入 `unified_sp` 框架

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md) Ring Attention SP 章节
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md) Ring Attention Overlap 章节

## Links

- [ulysses](ulysses.md)
- [ring-attention-overlap](../techniques/ring_attention_overlap.md)
- [dit](../modules/dit.md)
- [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [wan2.2-i2v](../models/wan2_2_i2v.md)
- [vggt](../../../spatial/concepts/models/vggt.md)（跨域·空间智能：VGGT SP overlap 用 Ring Attention）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)（Cosmos 长序列 Ring Attention）
- [context-parallel-train](../../../training/concepts/parallelism/context_parallel_train.md)（跨域·训练：MindSpeed Ring CP，KV 序列维 P2P 环形传递，含 Double Ring / LoongTrain 二级环与反向 KV 缓存）
