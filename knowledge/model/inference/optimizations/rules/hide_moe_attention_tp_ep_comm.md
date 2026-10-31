---
type: Optimization
title: 掩盖 MoE/attention 的 TP/EP 并行通信（共享专家异步 all_reduce / 通算融合算子）
description: 掩盖 MoE/attention 的 TP/EP 并行通信（共享专家异步 all_reduce / 通算融合算子）。MoE / attention 层里 TP / EP 引入的集合通信（路由专家规约的 all_reduce、QKV 投影前的 AllGather、O 投影后的 ReduceScatter）若与计算串行执行，通信时延完全暴露在关键路径上。两条掩盖路径按结构选用。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/218
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/305
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:32:47Z'
platforms:
- a2
---

# 掩盖 MoE/attention 的 TP/EP 并行通信（共享专家异步 all_reduce / 通算融合算子）

## 适用场景

MoE / attention 层里 [TP](../../concepts/parallelism/tensor_parallel.md) / [EP](../../concepts/parallelism/expert_parallel.md) 引入的集合通信（路由专家规约的 `all_reduce`、QKV 投影前的 `AllGather`、O 投影后的 `ReduceScatter`）若与计算串行执行，通信时延完全暴露在关键路径上。两条掩盖路径按结构选用。

## 路径一：共享专家计算掩盖路由专家 TP 规约（软件多流异步）

适用：任何"路由专家(TP) + 共享专家"并存的 MoE 结构（`moe_tp_size>1` 且有共享专家可作掩盖体）。路由专家按 TP 切分，各卡算完局部结果后必须一次跨卡 `all_reduce` 规约成完整输出；而共享专家 MLP 与该 all_reduce **无数据依赖**（吃同一份 `shared_mlp_input`、写不同张量）——具备用计算掩盖通信的条件。

手段（[多流并行](../../concepts/techniques/moe_multi_stream.md)）：

```python
# 1) 路由专家算完立即发起异步 all_reduce（不阻塞）
dist_moe = dist.all_reduce(hidden_states, group=moe_tp_group, async_op=True)
# 2) 通信在途时算共享专家 MLP —— 这段计算掩盖上面的通信
hidden_states_mlp = shared_mlp(shared_mlp_input)
# 3) 等路由专家 all_reduce 完成，再合并两路
dist_moe.wait()
output = hidden_states_mlp + combined_output
```

要点：`async_op=True` 是关键（同步 all_reduce 无法重叠）；`wait()` 落在两路相加之前保正确；共享专家计算越重、掩盖越充分。单卡或无共享专家时该重叠不成立。

## 路径二：通算融合算子替换串行"通信+MatMul"

适用：attention 的 QKV 投影前需 AllGather 聚合、O 投影后需 ReduceScatter 分发（TP/EP 沿 S 轴切分）。用 `torch_npu.npu_all_gather_base_mm`（AllGather+MM 融合）和 `torch_npu.npu_mm_reduce_scatter_base`（MM+ReduceScatter 融合）把通信与 MatMul 流水掩盖。

**硬约束（否则精度错）**：这两个融合算子**仅支持 2 维 tensor 输入、且只能对第 0 轴切分**。要切的是 S 轴时，须把 S、B 两轴合并成一维、且 **S 轴在前、B 在后**（`[b s h] -> [(s b) h]`；带 head 维 `[b n s d] -> [(s b) (n d)]`），算子调用后再 rearrange 回原 layout：

```python
npu_all_gather_base_mm(rearrange(x, 'b s h -> (s b) h'), weight.T, hccl_name, ep_size)
npu_mm_reduce_scatter_base(rearrange(o, 'b n s d -> (s b) (n d)'), weight.T, hccl_name, ep_size, reduce_op='sum')
```

权衡：合轴/复原引入额外 transpose 开销，但维护者对比确认"含额外 transpose 仍优于不使能融合的通算串行"。该融合算子走 MC2 路径，其平台/结构兼容性边界另见 [mc2-fused-comm-op-compatibility-fallback](../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)；相关通信域建法见 [hccl-comm-group-construction-pitfalls](hccl_comm_group_construction_pitfalls.md)。

> ⚠️ 曾有源文档正文写"s 轴必须在最内侧"，与代码 `(s b)`（S 在外）及维护者"S 轴在前"相反——以代码 + 维护者详复为准（`(s b)`，S 前 B 后）。

## 参考实现

- 路径一：HunyuanImage-3.0（`use_mixed_mlp_moe=True`）的 `moe_forward`。
- 路径二：HunyuanImage-3.0 的 `HunyuanImage3NpuFIA.forward`（Atlas A2/A3）。

## 相关经验

- 另见 [集合通信前的张量准备陷阱（行并行 bias 重复累加、zeros vs empty 覆写）](tensor_prep_before_hccl_collective.md)。
- 另见 [生成式推荐模型多卡——切超大 embedding 表（vocab-parallel + 阈值门控）](generative_recommender_vocab_parallel_embedding.md)。
- 另见 [大分辨率 VAE encode/decode 多卡空间并行（按算子选通信 + 边界 halo/overlap 补偿）](vae_multicard_spatial_parallel.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/218)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/305)（evidence）
