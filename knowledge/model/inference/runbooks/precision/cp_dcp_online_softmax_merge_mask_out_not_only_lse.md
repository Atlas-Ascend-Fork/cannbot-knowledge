---
type: Runbook
title: CP/DCP 在线-softmax 跨卡合并只 mask lse 不 mask out 污染归并——本卡对某序列无 KV 时须对 attn_out 施同一 batch_seq_mask 置 0
description: 昇腾 CP/DCP 解码 + P/D 分离下,KV 按 context-parallel 维切分后存在"本 CP rank 对某 batch 序列持有 0 份 KV token"的空位置(由 batch_seq_mask = num_computed_tokens_of_pcp_dcp[:,pcp_rank,dcp_rank]==0 标记)。每卡先用 FIA(npu_fused_infer_attention_score)算本地 attn_out 与 attn_lse,cat([out,lse])后跨卡 all_to_all/all_gather,再用在线-softmax 跨卡合并算子 npu_attention_update(lse_list, out_list, update_type)归并。failure_signature:对这些空位置只把 attn_lse 置 -inf、不屏蔽同位置 attn_out,会导致 attention 静默精度回退(accuracy issue),无报错、shape 正确。根因:合并算子以 out 与 lse 为两路独立输入,屏蔽 lse 不等于屏蔽 out,空 rank 的无意义 attn_out 污染归并。修法:在 lse 掩码前对称地对 attn_out 施加同一 batch_seq_mask、置 0(out_mask = batch_seq_mask[:,None,None].expand_as(attn_out); attn_out = torch.where(out_mask,0,attn_out))。可迁移边界:任何在昇腾上实现 CP/DCP 在线-softmax attention 跨卡归并(out+lse 两路合并)的实现都须对本卡无有效 KV 的位置同时屏蔽 out 与 lse;系于昇腾特有抓手(FIA 输出契约、npu_attention_update、PCP/DCP HCCL 归约),与具体模型无关。参考实现 vllm-ascend attention_cp.py::_forward_decode_pcp_dcp,复现于 Qwen P/D 分离。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5340
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# CP/DCP 在线-softmax 跨卡合并只 mask lse 不 mask out 污染归并——本卡对某序列无 KV 时须对 attn_out 施同一 batch_seq_mask 置 0

## 信号（现象）

在昇腾上做 [context parallel](../../concepts/parallelism/context_parallel.md) 解码 + P/D 分离，且各 CP rank 按序列切分 KV 缓存后，attention 精度异常（accuracy issue）——注意力输出偏离单卡/无 CP 基准，但没有报错、算子不 crash、shape 也对得上，是一种"静默精度回退"。

命中前提（核对自己是否真的落在本页范围内）：

- 解码路径每卡先用 [FIA](../../concepts/kernels/fused_infer_attention_score.md) 算出本卡本地的 `attn_out`(bs,H,v_head_dim) 与 `attn_lse`(bs,H,1)，`cat([out, lse])` 后跨卡 all_to_all（`dcp_size>1`）/ all_gather（`pcp_size>1`），再用一个**在线-softmax 跨卡合并算子**（本参考实现里是 `npu_attention_update`）归并出最终 attention。
- KV 按 CP 维切分后，存在"本 CP rank 对某个 batch 序列持有 0 份 KV token"的位置——P/D 分离下这非常常见（某些解码请求的 KV 恰好没落到本 rank）。
- 你的合并代码对这些空位置**只处理了 lse**（把 lse 置 `-inf`），没有对同位置的 `attn_out` 做任何屏蔽。

若你的注意力没有跨卡 out+lse 两路合并、或每卡都持有全量 KV（不存在"空 rank"位置），则不是本信号。

## 触发条件

- 空位置由 `batch_seq_mask = (num_computed_tokens_of_pcp_dcp[:, pcp_rank, dcp_rank] == 0)` 标记，即"本 CP rank 对该 batch 序列的已计算 KV token 数为 0"为 True。
- 这些空 rank 上，FIA 对"无有效 KV"的位置产出的 `attn_out` 是**未定义/无意义值**，却仍随 `cat([out, lse])` 进入合并算子。
- 只置 lse=-inf 不足以剔除该 out：合并算子以 out、lse 为两路独立输入（详见"根因"），屏蔽 lse 并不等于屏蔽 out，因此空 rank 的无效 out 会污染在线-softmax 归并结果。

> 合并算子内部"未屏蔽的无效 out 具体如何破坏归并"（例如即便对应权重≈0，garbage/NaN 是否仍经加权和传播）属未言明的微观机制推断，不作事实断言。确定的事实止于：**out 是合并算子独立的第二路输入，空 rank 的 out 必须显式置零**。

## 根因

在线-softmax 跨卡合并把每卡的 (out, lse) 两路一起喂给归并算子。对"本卡无有效 KV"的空位置只屏蔽 lse、不屏蔽 out，等于把无意义的本地注意力输出当作有效分片参与归并——lse 那条通道被清掉了，out 那条通道的脏值仍在。这是把"lse 掩码 == 剔除该分片"这一在 CUDA 侧单路合并里可能成立的直觉，错误迁移到"out/lse 两路独立输入"的昇腾合并算子上导致的。

## 修法

在对 lse 施掩码之前，**对称地对 `attn_out` 施加同一个 `batch_seq_mask`**，把空位置的 out 也置 0：

```python
out_mask = attn_metadata.decode_meta.batch_seq_mask[:, None, None].expand_as(attn_out)
attn_out = torch.where(out_mask, 0, attn_out)

lse_mask = attn_metadata.decode_meta.batch_seq_mask[:, None, None].expand_as(attn_lse)
attn_lse = torch.where(lse_mask, -torch.inf, attn_lse)   # 原有
```

要点：

- out 与 lse 用**同一个** `batch_seq_mask` 广播，只是各自 `expand_as` 到自己的形状；out 置 `0`、lse 置 `-inf`。
- 顺序上先补 out 的掩码、再走原有 lse 掩码；二者一起把空 rank 的整个分片"清零"，合并算子才不吃脏 out。
- 可读性重构（不改语义）：两段 mask 可合一——`mask = batch_seq_mask[:, None, None]; attn_out = where(mask, 0, attn_out); attn_lse = where(mask, -inf, attn_lse)`，靠广播省掉 `expand_as`。

## 可迁移边界

- 该陷阱系于昇腾特有抓手：FIA 的输出契约（out+lse 分离）、`npu_attention_update` 合并算子的两路输入形态、PCP/DCP 的 HCCL all_to_all / all_gather 归约路径；不是各硬件同名框架的通用逻辑。
- 但在此抓手内它是可迁移的：**任何在昇腾上实现 CP/DCP 在线-softmax attention 跨卡归并的实现**，对"本卡无有效 KV"的位置都必须同时屏蔽 out 与 lse，否则会撞同一精度陷阱——与具体模型无关（本参考实现的改动落在模型无关的 CP attention 后端，非某模型专属分支）。

## 参考实现及其约束

- vllm-ascend 昇腾 attention 后端 `vllm_ascend/attention/attention_cp.py`，函数 `_forward_decode_pcp_dcp`（PCP=prefill/persistent CP、DCP=decode CP 的解码分支）。
- 每卡：`torch_npu.npu_fused_infer_attention_score(query, k_nope, value, ...)` → 本地 `attn_out` / `attn_lse` → `cat([out, lse])` → DCP `all_to_all` / PCP `all_gather` → `_npu_attention_update`（内部 `torch_npu.npu_attention_update(lse_list, out_list, update_type)`）跨卡合并。
- `batch_seq_mask` 构造：`batch_seq_mask = (num_computed_tokens_of_pcp_dcp[:, pcp_rank, dcp_rank] == 0)`。
- 约束（属该参考实现、非技术本身）：修复以 `torch.where` + `expand_as` 广播落地；复现于 Qwen 的 P/D 分离场景，但改动通用。维护者直接合并（备注 CI 因已知问题失败故手动合入），评审确认改动 logically sound。**源未给出 before→after 的具体精度数字**，correctness 依据为 diff 事实 + 维护者/评审确认。

## 相关经验
- [CP chunked-prefill 空 KV 分片返回 None 破 LSE 合并——须返](../runtime/cp_prefill_empty_kv_shard_none_lse_merge.md)

## Evidence

- 改动（合并态，5 增 1 文件）：`attention_cp.py` 在 lse 掩码前新增 `out_mask = batch_seq_mask[:,None,None].expand_as(attn_out); attn_out = torch.where(out_mask, 0, attn_out)`；相关上下文为 `_forward_decode_pcp_dcp`、`batch_seq_mask` 构造与 `_npu_attention_update` / `npu_attention_update`。
- 合并 commit `1858f3d36ecd649257c81a8699aae2ba84ee68b8`；由维护者合并（备注 CI 因已知问题失败故手动合入），评审确认改动「correctly applying a mask to the attention output (attn_out) during the decode phase … logically sound and addresses the intended bug」。
- 溯源下探：[vllm-ascend-pr-5340-bugfix-fix-qwen-p-d-disaggregation-accuracy-issue](https://github.com/vllm-project/vllm-ascend/pull/5340)